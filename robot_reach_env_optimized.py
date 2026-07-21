"""
优化版机械臂到达环境
优化内容：
1. 缩小目标范围到更容易到达的区域
2. 增加到达奖励权重
3. 减小动作惩罚鼓励积极探索
4. 混合采样策略：50%薄弱区域 + 50%全范围
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pybullet as p
import pybullet_data
import gc


class RobotReachEnvOptimized(gym.Env):
    """优化版机械臂到达环境"""

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 60}

    def __init__(self, render_mode=None, max_steps=500, use_weighted_sampling=True, dynamic_target=False):
        super().__init__()

        self.render_mode = render_mode
        self.max_steps = max_steps
        self.step_count = 0
        self.use_weighted_sampling = use_weighted_sampling
        self.dynamic_target = dynamic_target

        # 动作空间
        self.action_space = spaces.Box(
            low=-1.0, high=1.0, shape=(7,), dtype=np.float32
        )

        # 观测空间
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(20,), dtype=np.float32
        )

        # 连接物理引擎
        if render_mode == "human":
            self.physics_client = p.connect(p.GUI)
            p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)
        else:
            self.physics_client = p.connect(p.DIRECT)

        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(0, 0, -9.81)
        p.setTimeStep(1 / 240.0)

        self.robot_id = None
        self.target_pos = None
        self.target_body_id = None

        # 优化后的超参数
        self.action_scale = 0.05
        self.reach_threshold = 0.03
        self.reach_reward = 50.0
        self.action_penalty = 0.0005
        self.sub_steps = 4

        # 扩展目标范围以增强泛化能力
        # Original: X[0.40,0.50], Y[-0.10,0.10], Z[0.30,0.40]
        # Extended: X[0.25,0.65], Y[-0.25,0.25], Z[0.20,0.55]
        self.target_min = np.array([0.25, -0.25, 0.20], dtype=np.float32)
        self.target_max = np.array([0.65, 0.25, 0.55], dtype=np.float32)

        # 薄弱区域范围（可达但困难的区域）
        # 排除物理不可达点：(0.25, ±0.10, 0.35) IK误差>0.14m
        self.weak_min = np.array([0.25, -0.25, 0.30], dtype=np.float32)
        self.weak_max = np.array([0.40, 0.25, 0.55], dtype=np.float32)

        # 动态目标相关参数
        self.trajectory_type = None
        self.trajectory_params = None
        self.target_speed = None
        self.stable_count = 0
        self.stable_threshold = 5

    def _is_reachable(self, pos):
        """检查目标位置是否可达（IK求解误差<0.1m）"""
        if self.robot_id is None:
            return True
        ik_solution = p.calculateInverseKinematics(self.robot_id, 6, list(pos))
        p.setJointMotorControlArray(self.robot_id, range(7), p.POSITION_CONTROL, targetPositions=ik_solution)
        for _ in range(50):
            p.stepSimulation()
        ee_pos = np.array(p.getLinkState(self.robot_id, 6)[0])
        dist = np.linalg.norm(ee_pos - np.array(pos))
        return dist < 0.1

    def _sample_target(self):
        """混合采样策略"""
        if self.use_weighted_sampling and self.np_random.random() < 0.5:
            target = self.np_random.uniform(self.weak_min, self.weak_max).astype(np.float32)
        else:
            target = self.np_random.uniform(self.target_min, self.target_max).astype(np.float32)

        max_attempts = 100
        for _ in range(max_attempts):
            if self._is_reachable(target):
                return target
            if self.use_weighted_sampling and self.np_random.random() < 0.5:
                target = self.np_random.uniform(self.weak_min, self.weak_max).astype(np.float32)
            else:
                target = self.np_random.uniform(self.target_min, self.target_max).astype(np.float32)

        return self.np_random.uniform(self.target_min, self.target_max).astype(np.float32)

    def _generate_trajectory(self):
        """生成动态目标轨迹"""
        self.trajectory_type = self.np_random.choice(['linear', 'sinusoidal'])
        self.target_speed = self.np_random.uniform(0.05, 0.1)

        if self.trajectory_type == 'linear':
            start_pos = self._sample_target()
            direction = self.np_random.uniform(-1, 1, size=3)
            direction = direction / np.linalg.norm(direction)
            max_distance = 0.3
            end_pos = start_pos + direction * max_distance
            end_pos = np.clip(end_pos, self.target_min, self.target_max)
            self.trajectory_params = {
                'start': start_pos,
                'end': end_pos,
                'total_time': np.linalg.norm(end_pos - start_pos) / self.target_speed
            }
            return start_pos

        else:
            center = self._sample_target()
            amplitude = np.array([
                self.np_random.uniform(0.05, 0.15),
                self.np_random.uniform(0.05, 0.15),
                self.np_random.uniform(0.05, 0.10)
            ])
            frequency = self.np_random.uniform(0.5, 1.5)
            self.trajectory_params = {
                'center': center,
                'amplitude': amplitude,
                'frequency': frequency
            }
            return center

    def _update_target_position(self):
        """根据轨迹更新目标位置"""
        if not self.dynamic_target or self.trajectory_type is None:
            return

        elapsed_time = self.step_count * (1 / 240.0) * self.sub_steps

        if self.trajectory_type == 'linear':
            start = self.trajectory_params['start']
            end = self.trajectory_params['end']
            total_time = self.trajectory_params['total_time']

            if total_time > 0:
                t = min(elapsed_time / total_time, 1.0)
            else:
                t = 1.0

            new_pos = start + t * (end - start)

        else:
            center = self.trajectory_params['center']
            amplitude = self.trajectory_params['amplitude']
            frequency = self.trajectory_params['frequency']

            new_pos = center + amplitude * np.sin(2 * np.pi * frequency * elapsed_time)

        new_pos = np.clip(new_pos, self.target_min, self.target_max)
        self.target_pos = new_pos.astype(np.float32)

        if self.target_body_id is not None:
            try:
                p.removeBody(self.target_body_id)
            except:
                pass
            vis_shape_id = p.createVisualShape(
                p.GEOM_SPHERE, radius=0.03, rgbaColor=[1, 0, 0, 0.8]
            )
            self.target_body_id = p.createMultiBody(
                baseMass=0,
                baseVisualShapeIndex=vis_shape_id,
                basePosition=self.target_pos
            )

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        p.resetSimulation()
        p.setGravity(0, 0, -9.81)
        p.setTimeStep(1 / 240.0)
        p.loadURDF("plane.urdf")

        self.robot_id = p.loadURDF(
            "kuka_iiwa/model.urdf", [0, 0, 0], useFixedBase=True
        )

        # 混合采样策略：50%薄弱区域 + 50%全范围，带可达性验证
        if self.dynamic_target:
            self.target_pos = self._generate_trajectory()
        else:
            self.target_pos = self._sample_target()

        # 创建目标可视化
        if self.target_body_id is not None:
            try:
                p.removeBody(self.target_body_id)
            except:
                pass
        vis_shape_id = p.createVisualShape(
            p.GEOM_SPHERE, radius=0.03, rgbaColor=[1, 0, 0, 0.8]
        )
        self.target_body_id = p.createMultiBody(
            baseMass=0,
            baseVisualShapeIndex=vis_shape_id,
            basePosition=self.target_pos
        )

        # 扩大初始关节范围以增强泛化能力
        # Original: uniform(-0.5, 0.5)
        # Extended: uniform(-1.0, 1.0)
        for i in range(7):
            p.resetJointState(
                self.robot_id, i,
                self.np_random.uniform(-1.0, 1.0)
            )

        self.step_count = 0
        self.stable_count = 0

        for _ in range(10):
            p.stepSimulation()

        return self._get_obs(), {}

    def step(self, action):
        action = np.clip(action, -1.0, 1.0) * self.action_scale

        states = p.getJointStates(self.robot_id, range(7))
        current_positions = np.array([s[0] for s in states])

        target_positions = current_positions + action
        for i in range(7):
            p.setJointMotorControl2(
                self.robot_id, i,
                p.POSITION_CONTROL,
                targetPosition=target_positions[i],
                force=240
            )

        for _ in range(self.sub_steps):
            p.stepSimulation()

        self.step_count += 1

        self._update_target_position()

        obs = self._get_obs()
        ee_pos = np.array(p.getLinkState(self.robot_id, 6)[0])
        dist = np.linalg.norm(ee_pos - self.target_pos)

        # 优化后的奖励函数
        reward = -dist * 10.0

        if dist < self.reach_threshold:
            self.stable_count += 1
            reward += 2.0
            if self.stable_count >= self.stable_threshold:
                reward += self.reach_reward
                terminated = True
            else:
                terminated = False
        else:
            self.stable_count = 0
            terminated = False

        reward -= self.action_penalty * np.sum(np.square(action))

        truncated = self.step_count >= self.max_steps

        info = {
            "distance": dist,
            "success": terminated,
            "step": self.step_count,
            "target_pos": self.target_pos.copy()
        }

        return obs, reward, terminated, truncated, info

    def _get_obs(self):
        states = p.getJointStates(self.robot_id, range(7))
        joint_pos = np.array([s[0] for s in states], dtype=np.float32)
        joint_vel = np.array([s[1] for s in states], dtype=np.float32)
        ee_pos = np.array(p.getLinkState(self.robot_id, 6)[0], dtype=np.float32)

        return np.concatenate([
            joint_pos, joint_vel, ee_pos, self.target_pos
        ], dtype=np.float32)

    def render(self):
        if self.render_mode == "rgb_array":
            width, height = 640, 480
            view_matrix = p.computeViewMatrix(
                cameraEyePosition=[1.5, 0, 1.2],
                cameraTargetPosition=[0, 0, 0.5],
                cameraUpVector=[0, 0, 1]
            )
            proj_matrix = p.computeProjectionMatrixFOV(
                fov=60, aspect=width / height,
                nearVal=0.1, farVal=100
            )
            _, _, rgb, _, _ = p.getCameraImage(
                width, height, view_matrix, proj_matrix
            )
            return np.array(rgb)[:, :, :3]

    def close(self):
        if self.physics_client >= 0:
            try:
                p.disconnect(self.physics_client)
                self.physics_client = -1
            except:
                pass
        gc.collect()

    def __del__(self):
        self.close()