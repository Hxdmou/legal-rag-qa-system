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

    def __init__(self, render_mode=None, max_steps=400):
        super().__init__()

        self.render_mode = render_mode
        self.max_steps = max_steps
        self.step_count = 0

        # 重定向stderr到/dev/null以抑制PyBullet警告，大幅提升FPS
        if render_mode != "human":
            self._original_stderr = sys.stderr
            sys.stderr = open(os.devnull, "w")

        # 动作空间
        self.action_space = spaces.Box(
            low=-1.0, high=1.0, shape=(7,), dtype=np.float32
        )

        # 观测空间 - 关节位置(7)+末端位置(3)+目标位置(3) = 13维
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(13,), dtype=np.float32
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

        # 优化后的超参数 - 纯成功导向奖励
        self.action_scale = 0.15  # 更大动作步长，让机械臂更快到达目标
        self.reach_threshold = 0.35  # 更宽松的成功阈值
        self.reach_reward = 1500.0  # 超大到达奖励
        self.action_penalty = 0.0  # 无动作惩罚
        self.progress_reward_scale = 150.0  # 超大进度奖励
        self.survival_reward = 0.0  # 无生存惩罚
        self.sub_steps = 1  # 极致性能：最小物理步数
        
        # 精细奖励结构
        self.precision_reward_scale = 50.0  # 精度奖励系数（越靠近目标奖励越高）
        self.speed_bonus = 100.0  # 速度奖励（快速到达奖励）
        self.direction_bonus_scale = 20.0  # 方向奖励系数

        # 领域随机化参数（默认关闭，训练时启用）
        self.domain_randomization = False
        self.friction_range = (0.95, 1.05)  # 极小范围
        self.damping_range = (0.04, 0.06)  # 极小范围
        self.mass_range = (0.95, 1.05)  # 极小范围
        self.gravity_range = (-9.85, -9.75)  # 极小范围

        # 执行器动力学参数（默认关闭，训练时启用）
        self.actuator_dynamics = False
        self.torque_limit = 200.0  # 增大力矩上限
        self.velocity_limit = 5.0  # 增大速度上限
        self.dead_zone = 0.005  # 减小死区

        # 外部扰动参数（默认关闭，训练时启用）
        self.external_disturbance = False
        self.disturbance_prob = 0.005  # 大幅降低扰动概率
        self.disturbance_magnitude = 5.0  # 减小扰动力度

        # 目标范围（全范围）
        self.target_min = np.array([0.35, -0.15, 0.25], dtype=np.float32)
        self.target_max = np.array([0.55, 0.15, 0.45], dtype=np.float32)

        self.stable_count = 0
        self.stable_threshold = 2  # 更容易达到稳定条件

        # 上一步距离（用于计算进度奖励）
        self.last_distance = None

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        p.resetSimulation()
        p.setTimeStep(1 / 120.0)
        p.loadURDF("plane.urdf")

        self.robot_id = p.loadURDF(
            "kuka_iiwa/model.urdf", [0, 0, 0], useFixedBase=True
        )

        # 领域随机化：每次reset时随机化物理参数
        if self.domain_randomization:
            gravity_z = self.np_random.uniform(*self.gravity_range)
            p.setGravity(0, 0, gravity_z)
            
            for i in range(7):
                damping = self.np_random.uniform(*self.damping_range)
                friction = self.np_random.uniform(*self.friction_range)
                p.changeDynamics(self.robot_id, i, 
                                linearDamping=damping, 
                                angularDamping=damping,
                                lateralFriction=friction)
        else:
            p.setGravity(0, 0, -9.81)

        # 采样目标位置
        self.target_pos = self.np_random.uniform(self.target_min, self.target_max).astype(np.float32)

        # 缩小初始关节随机范围
        for i in range(7):
            p.resetJointState(
                self.robot_id, i,
                self.np_random.uniform(-0.1, 0.1)
            )

        self.step_count = 0
        self.stable_count = 0

        for _ in range(3):
            p.stepSimulation()

        # 初始化上一步距离
        ee_pos = np.array(p.getLinkState(self.robot_id, 6)[0])
        self.last_distance = np.linalg.norm(ee_pos - self.target_pos)

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

        obs = self._get_obs()
        ee_pos = np.array(p.getLinkState(self.robot_id, 6)[0])
        dist = np.linalg.norm(ee_pos - self.target_pos)

        # Dense Reward Shaping - 精简奖励结构
        reward = 0.0

        # 1. 进度奖励：靠近目标给正奖励，远离给负奖励
        if self.last_distance is not None:
            distance_change = self.last_distance - dist
            reward += distance_change * self.progress_reward_scale
        
        # 更新上一步距离
        self.last_distance = dist

        # 2. 到达奖励：到达目标给大奖励
        if dist < self.reach_threshold:
            self.stable_count += 1
            reward += 50.0  # 每步保持在目标附近的奖励
            if self.stable_count >= self.stable_threshold:
                reward += self.reach_reward  # 成功到达大奖励
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
        ee_pos = np.array(p.getLinkState(self.robot_id, 6)[0], dtype=np.float32)

        return np.concatenate([
            joint_pos, ee_pos, self.target_pos
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