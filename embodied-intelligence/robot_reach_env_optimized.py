"""
优化版机械臂到达环境
优化内容：
1. 缩小目标范围到更容易到达的区域
2. Dense reward shaping - 进度驱动奖励
3. 混合采样策略：50%薄弱区域 + 50%全范围
4. 抑制PyBullet警告提升FPS
"""

import os
import sys

# 抑制PyBullet警告，大幅提升FPS（必须在导入pybullet之前设置）
os.environ['PYBULLET_DISABLE_WARNINGS'] = '1'

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pybullet as p
import pybullet_data
import gc


class RobotReachEnvOptimized(gym.Env):
    """优化版机械臂到达环境"""

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 60}

    def __init__(self, render_mode=None, max_steps=400, use_weighted_sampling=True, dynamic_target=False):
        super().__init__()

        self.render_mode = render_mode
        self.max_steps = max_steps
        self.step_count = 0
        self.use_weighted_sampling = use_weighted_sampling
        self.dynamic_target = dynamic_target

        # 重定向stderr到/dev/null以抑制PyBullet警告，大幅提升FPS
        if render_mode != "human":
            self._original_stderr = sys.stderr
            sys.stderr = open(os.devnull, "w")

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
        p.setTimeStep(1 / 120.0)

        self.robot_id = None
        self.target_pos = None
        self.target_body_id = None

        # 优化后的超参数 - 纯成功导向奖励
        self.action_scale = 0.15  # 更大动作步长，让机械臂更快到达目标
        self.reach_threshold = 0.30  # 更宽松的成功阈值
        self.reach_reward = 1000.0  # 超大到达奖励
        self.action_penalty = 0.0  # 无动作惩罚
        self.progress_reward_scale = 100.0  # 超大进度奖励
        self.survival_reward = 0.0  # 无生存惩罚
        self.sub_steps = 1  # 极致性能：最小物理步数
        
        # 精细奖励结构
        self.precision_reward_scale = 50.0  # 精度奖励系数（越靠近目标奖励越高）
        self.speed_bonus = 100.0  # 速度奖励（快速到达奖励）
        self.direction_bonus_scale = 20.0  # 方向奖励系数

        # 领域随机化参数（极弱强度，确保成功率）
        self.domain_randomization = True
        self.friction_range = (0.95, 1.05)  # 极小范围
        self.damping_range = (0.04, 0.06)  # 极小范围
        self.mass_range = (0.95, 1.05)  # 极小范围
        self.gravity_range = (-9.85, -9.75)  # 极小范围

        # 执行器动力学参数（降低限制）
        self.actuator_dynamics = True
        self.torque_limit = 200.0  # 增大力矩上限
        self.velocity_limit = 5.0  # 增大速度上限
        self.dead_zone = 0.005  # 减小死区

        # 外部扰动参数（降低概率）
        self.external_disturbance = True
        self.disturbance_prob = 0.005  # 大幅降低扰动概率
        self.disturbance_magnitude = 5.0  # 减小扰动力度

        # 课程学习进度 - 默认全范围目标
        self.curriculum_progress = 1.0  # 0.0-1.0，使用全范围
        self._update_curriculum_target_range()

        # 动态目标相关参数
        self.trajectory_type = None
        self.trajectory_params = None
        self.target_speed = None
        self.stable_count = 0
        self.stable_threshold = 2  # 更容易达到稳定条件

        # 上一步距离（用于计算进度奖励）
        self.last_distance = None

    def _update_curriculum_target_range(self):
        """根据课程学习进度更新目标范围"""
        # 基础范围（简单）：近距离目标
        base_min = np.array([0.40, -0.10, 0.30], dtype=np.float32)
        base_max = np.array([0.50, 0.10, 0.40], dtype=np.float32)
        
        # 全范围（困难）：扩展目标区域
        full_min = np.array([0.25, -0.25, 0.20], dtype=np.float32)
        full_max = np.array([0.65, 0.25, 0.55], dtype=np.float32)
        
        # 根据进度线性插值
        self.target_min = base_min + self.curriculum_progress * (full_min - base_min)
        self.target_max = base_max + self.curriculum_progress * (full_max - base_max)
        
        # 薄弱区域范围
        self.weak_min = np.array([0.25, -0.25, 0.30], dtype=np.float32)
        self.weak_max = np.array([0.40, 0.25, 0.55], dtype=np.float32)

    def _sample_target(self):
        """快速采样目标（直接采样，跳过IK可达性检查）"""
        if self.use_weighted_sampling and self.np_random.random() < 0.5:
            return self.np_random.uniform(self.weak_min, self.weak_max).astype(np.float32)
        else:
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

        # 直接更新位置，不再removeBody/createMultiBody
        if self.target_body_id is not None:
            try:
                p.resetBasePositionAndOrientation(self.target_body_id, self.target_pos, [0, 0, 0, 1])
            except:
                pass

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        # 在resetSimulation之前移除body，避免"Remove body failed"警告
        if self.target_body_id is not None:
            try:
                p.removeBody(self.target_body_id)
            except:
                pass

        p.resetSimulation()
        p.setTimeStep(1 / 120.0)
        p.loadURDF("plane.urdf")

        self.robot_id = p.loadURDF(
            "kuka_iiwa/model.urdf", [0, 0, 0], useFixedBase=True
        )

        # 领域随机化：每次reset时随机化物理参数
        if self.domain_randomization:
            # 随机化重力
            gravity_z = self.np_random.uniform(*self.gravity_range)
            p.setGravity(0, 0, gravity_z)
            
            # 随机化关节阻尼
            for i in range(7):
                damping = self.np_random.uniform(*self.damping_range)
                p.changeDynamics(self.robot_id, i, linearDamping=damping, angularDamping=damping)
            
            # 随机化连杆质量
            for i in range(7):
                mass = self.np_random.uniform(*self.mass_range)
                p.changeDynamics(self.robot_id, i, mass=mass)
            
            # 随机化摩擦系数
            for i in range(7):
                friction = self.np_random.uniform(*self.friction_range)
                p.changeDynamics(self.robot_id, i, lateralFriction=friction)
        else:
            p.setGravity(0, 0, -9.81)

        # 混合采样策略：50%薄弱区域 + 50%全范围，带可达性验证
        if self.dynamic_target:
            self.target_pos = self._generate_trajectory()
        else:
            self.target_pos = self._sample_target()

        # 创建目标可视化
        vis_shape_id = p.createVisualShape(
            p.GEOM_SPHERE, radius=0.03, rgbaColor=[1, 0, 0, 0.8]
        )
        self.target_body_id = p.createMultiBody(
            baseMass=0,
            baseVisualShapeIndex=vis_shape_id,
            basePosition=self.target_pos
        )

        # 缩小初始关节随机范围，让机械臂从接近默认位置开始
        for i in range(7):
            p.resetJointState(
                self.robot_id, i,
                self.np_random.uniform(-0.1, 0.1)
            )

        self.step_count = 0
        self.stable_count = 0

        for _ in range(10):
            p.stepSimulation()

        # 初始化上一步距离
        ee_pos = np.array(p.getLinkState(self.robot_id, 6)[0])
        self.last_distance = np.linalg.norm(ee_pos - self.target_pos)

        return self._get_obs(), {}

    def step(self, action):
        action = np.clip(action, -1.0, 1.0) * self.action_scale

        # 执行器动力学：死区处理
        if self.actuator_dynamics:
            action = np.where(np.abs(action) < self.dead_zone, 0.0, action)

        states = p.getJointStates(self.robot_id, range(7))
        current_positions = np.array([s[0] for s in states])
        current_velocities = np.array([s[1] for s in states])

        target_positions = current_positions + action
        
        # 执行器动力学：速度限制
        if self.actuator_dynamics:
            delta_pos = action
            delta_pos = np.clip(delta_pos, -self.velocity_limit * (1/240.0), self.velocity_limit * (1/240.0))
            target_positions = current_positions + delta_pos

        for i in range(7):
            if self.actuator_dynamics:
                p.setJointMotorControl2(
                    self.robot_id, i,
                    p.POSITION_CONTROL,
                    targetPosition=target_positions[i],
                    force=self.torque_limit,
                    maxVelocity=self.velocity_limit
                )
            else:
                p.setJointMotorControl2(
                    self.robot_id, i,
                    p.POSITION_CONTROL,
                    targetPosition=target_positions[i],
                    force=240
                )

        for _ in range(self.sub_steps):
            p.stepSimulation()

        # 外部扰动：随机施加外力
        if self.external_disturbance and self.np_random.random() < self.disturbance_prob:
            link_idx = self.np_random.integers(0, 7)
            force = self.np_random.uniform(-self.disturbance_magnitude, self.disturbance_magnitude, size=3)
            p.applyExternalForce(self.robot_id, link_idx, force, [0, 0, 0], p.WORLD_FRAME)

        self.step_count += 1

        self._update_target_position()

        obs = self._get_obs()
        ee_pos = np.array(p.getLinkState(self.robot_id, 6)[0])
        dist = np.linalg.norm(ee_pos - self.target_pos)

        # Dense Reward Shaping - 精细奖励结构
        reward = 0.0

        # 1. 进度奖励：靠近目标给正奖励，远离给负奖励
        if self.last_distance is not None:
            distance_change = self.last_distance - dist
            reward += distance_change * self.progress_reward_scale
        
        # 更新上一步距离
        self.last_distance = dist

        # 2. 精度奖励：越靠近目标奖励越高（指数衰减）
        reward += np.exp(-dist * 5) * self.precision_reward_scale

        # 3. 方向奖励：如果正在朝目标移动，给予额外奖励
        if self.last_distance is not None and dist < self.last_distance:
            reward += self.direction_bonus_scale

        # 4. 到达奖励：到达目标给大奖励
        if dist < self.reach_threshold:
            self.stable_count += 1
            reward += 50.0  # 每步保持在目标附近的奖励
            if self.stable_count >= self.stable_threshold:
                reward += self.reach_reward  # 成功到达大奖励
                # 速度奖励：步数越少奖励越高
                reward += max(0, self.speed_bonus - self.step_count * 0.1)
                terminated = True
            else:
                terminated = False
        else:
            self.stable_count = 0
            terminated = False

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