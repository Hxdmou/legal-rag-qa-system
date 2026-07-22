"""
增强版机械臂训练脚本 - 集成仿真增强模块
核心特性：
1. 领域随机化 - 训练中随机化物理参数
2. 通信延迟仿真 - 模拟控制延迟和状态读取延迟
3. 执行器动力学 - 模拟真实电机限制
4. 外部扰动仿真 - 模拟真实世界干扰
5. 传感器噪声 - 模拟传感器误差
6. 安全保障 - 内存限制、异常监控、自动恢复
"""

import gc
import time
import psutil
import numpy as np
import os
import signal

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv, VecMonitor
from stable_baselines3.common.callbacks import (
    BaseCallback,
    EvalCallback,
    CheckpointCallback
)

from domain_randomization import DomainRandomizationSystem
from latency_simulator import LatencySystem
from actuator_dynamics import ActuatorSystem
from disturbance_simulator import DisturbanceSystem
from sensor_noise import SensorNoiseSystem


class EnhancedRobotReachEnv:
    """增强版机械臂到达环境（集成仿真增强模块）"""
    
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 60}

    def __init__(self, render_mode=None, max_steps=500):
        import pybullet as p
        import pybullet_data
        
        self.render_mode = render_mode
        self.max_steps = max_steps
        self.step_count = 0
        self.p = p
        
        # 动作空间
        self.action_space = __import__('gymnasium').spaces.Box(
            low=-1.0, high=1.0, shape=(7,), dtype=np.float32
        )

        # 观测空间
        self.observation_space = __import__('gymnasium').spaces.Box(
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

        # 超参数
        self.action_scale = 0.05
        self.reach_threshold = 0.03
        self.reach_reward = 50.0
        self.action_penalty = 0.0005
        self.sub_steps = 4

        # 扩展目标范围
        self.target_min = np.array([0.25, -0.25, 0.20], dtype=np.float32)
        self.target_max = np.array([0.65, 0.25, 0.55], dtype=np.float32)
        
        # 薄弱区域
        self.weak_min = np.array([0.25, -0.25, 0.30], dtype=np.float32)
        self.weak_max = np.array([0.40, 0.25, 0.55], dtype=np.float32)

        # 初始化仿真增强模块
        self._init_enhancement_modules()

    def _init_enhancement_modules(self):
        """初始化所有仿真增强模块"""
        
        # 领域随机化 - 训练中定期随机化物理参数
        self.domain_randomizer = DomainRandomizationSystem({
            "enabled": True,
            "domain_randomizer": {
                "enabled": True,
                "randomize_interval": 30.0,
                "friction_range": [0.4, 0.6],
                "damping_range": [0.02, 0.08],
                "mass_range": [0.95, 1.05],
                "gravity_range": [-9.85, -9.75]
            },
            "mass_randomizer": {"enabled": False},
            "friction_randomizer": {"enabled": False},
            "physics_distortion": {"enabled": False}
        })
        
        # 通信延迟 - 模拟控制延迟
        self.latency_system = LatencySystem({
            "enabled": True,
            "latency_simulator": {"enabled": True, "mean_latency_ms": 5},
            "control_delay": {"enabled": True, "delay_ms": 3},
            "state_delay": {"enabled": True, "delay_ms": 2},
            "network_latency": {"enabled": False}  # 训练时不启用网络延迟，避免训练不稳定
        })
        
        # 执行器动力学 - 模拟电机限制
        self.actuator_system = ActuatorSystem({
            "enabled": True,
            "actuator_dynamics": {
                "enabled": True,
                "max_torque": 50.0,
                "max_velocity": 3.0,
                "max_acceleration": 15.0,
                "dead_zone": 0.0005
            },
            "motor_model": {"enabled": False},
            "joint_constraint": {"enabled": True, "max_force": 240.0}
        })
        
        # 外部扰动 - 模拟真实世界干扰
        self.disturbance_system = DisturbanceSystem({
            "enabled": True,
            "disturbance_simulator": {
                "enabled": True,
                "periodic_force_magnitude": 2.0,
                "impulse_probability": 0.01,
                "vibration_magnitude": 0.005
            },
            "impact_simulator": {"enabled": False},
            "load_simulator": {"enabled": False}
        })
        
        # 传感器噪声 - 模拟传感器误差
        self.noise_system = SensorNoiseSystem({
            "enabled": True,
            "gaussian_noise": {"enabled": True, "std_dev": 0.0005},
            "quantization_noise": {"enabled": True, "resolution": 0.001},
            "drift_noise": {"enabled": True, "drift_rate": 0.0001},
            "jitter_noise": {"enabled": True, "jitter_amplitude": 0.0002}
        })
        
        print("[ENHANCEMENT] 所有仿真增强模块已初始化")

    def _is_reachable(self, pos):
        """检查目标位置是否可达"""
        if self.robot_id is None:
            return True
        p = self.p
        ik_solution = p.calculateInverseKinematics(self.robot_id, 6, list(pos))
        p.setJointMotorControlArray(self.robot_id, range(7), p.POSITION_CONTROL, targetPositions=ik_solution)
        for _ in range(50):
            p.stepSimulation()
        ee_pos = np.array(p.getLinkState(self.robot_id, 6)[0])
        dist = np.linalg.norm(ee_pos - np.array(pos))
        return dist < 0.1

    def _sample_target(self):
        """混合采样策略"""
        rng = np.random.RandomState()
        if rng.random() < 0.5:
            target = rng.uniform(self.weak_min, self.weak_max).astype(np.float32)
        else:
            target = rng.uniform(self.target_min, self.target_max).astype(np.float32)

        max_attempts = 100
        for _ in range(max_attempts):
            if self._is_reachable(target):
                return target
            if rng.random() < 0.5:
                target = rng.uniform(self.weak_min, self.weak_max).astype(np.float32)
            else:
                target = rng.uniform(self.target_min, self.target_max).astype(np.float32)

        return rng.uniform(self.target_min, self.target_max).astype(np.float32)

    def reset(self, seed=None):
        p = self.p
        
        if seed is not None:
            np.random.seed(seed)
        
        p.resetSimulation()
        p.setGravity(0, 0, -9.81)
        p.setTimeStep(1 / 240.0)
        p.loadURDF("plane.urdf")

        self.robot_id = p.loadURDF(
            "kuka_iiwa/model.urdf", [0, 0, 0], useFixedBase=True
        )

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

        # 扩大初始关节范围
        for i in range(7):
            p.resetJointState(
                self.robot_id, i,
                np.random.uniform(-1.0, 1.0)
            )

        self.step_count = 0
        
        # 重置增强模块状态
        self.domain_randomizer.reset()
        self.disturbance_system.reset()
        self.actuator_system.reset()

        for _ in range(10):
            p.stepSimulation()

        return self._get_obs(), {}

    def step(self, action):
        p = self.p
        
        action = np.clip(action, -1.0, 1.0) * self.action_scale

        # 应用通信延迟
        self.latency_system.apply_control_latency()

        states = p.getJointStates(self.robot_id, range(7))
        current_positions = np.array([s[0] for s in states])
        current_velocities = np.array([s[1] for s in states])

        # 应用执行器动力学限制
        if self.actuator_system.is_enabled():
            limited_commands = []
            for i in range(7):
                limited_cmd, _ = self.actuator_system.actuator_dynamics.apply_all_limits(
                    i, action[i], current_velocities[i], 1/240.0
                )
                limited_commands.append(limited_cmd)
            action = np.array(limited_commands)

        target_positions = current_positions + action
        for i in range(7):
            p.setJointMotorControl2(
                self.robot_id, i,
                p.POSITION_CONTROL,
                targetPosition=target_positions[i],
                force=240
            )

        # 应用外部扰动
        if self.disturbance_system.is_enabled():
            self.disturbance_system.apply_disturbances(self.robot_id, 6)

        for _ in range(self.sub_steps):
            p.stepSimulation()

        # 应用领域随机化（周期性）
        if self.domain_randomizer.is_enabled():
            self.domain_randomizer.check_and_randomize(self.robot_id, list(range(7)))

        self.step_count += 1

        obs = self._get_obs()
        ee_pos = np.array(p.getLinkState(self.robot_id, 6)[0])
        
        # 应用传感器噪声
        if self.noise_system.is_enabled():
            ee_pos = self.noise_system.apply_ee_noise(ee_pos.tolist())
            ee_pos = np.array(ee_pos)

        dist = np.linalg.norm(ee_pos - self.target_pos)

        # 奖励函数
        reward = -dist * 10.0

        if dist < self.reach_threshold:
            reward += 52.0
            terminated = True
        else:
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
        p = self.p
        
        states = p.getJointStates(self.robot_id, range(7))
        joint_pos = np.array([s[0] for s in states], dtype=np.float32)
        joint_vel = np.array([s[1] for s in states], dtype=np.float32)
        
        # 应用传感器噪声到关节状态
        if self.noise_system.is_enabled():
            joint_pos = np.array(self.noise_system.apply_joint_noise(joint_pos.tolist()), dtype=np.float32)

        ee_pos = np.array(p.getLinkState(self.robot_id, 6)[0], dtype=np.float32)
        
        # 应用传感器噪声到末端位置
        if self.noise_system.is_enabled():
            ee_pos = np.array(self.noise_system.apply_ee_noise(ee_pos.tolist()), dtype=np.float32)

        return np.concatenate([
            joint_pos, joint_vel, ee_pos, self.target_pos
        ], dtype=np.float32)

    def render(self):
        if self.render_mode == "rgb_array":
            p = self.p
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
                self.p.disconnect(self.physics_client)
                self.physics_client = -1
            except:
                pass
        gc.collect()

    def __del__(self):
        self.close()


def make_env(rank, seed=0):
    def _init():
        env = EnhancedRobotReachEnv(render_mode=None, max_steps=500)
        env.reset(seed=seed + rank)
        return env
    return _init


class SafeResourceMonitor(BaseCallback):
    """安全资源监控 - 防止内存耗尽"""

    def __init__(self, check_freq=1000, memory_threshold=75, verbose=1):
        super().__init__(verbose)
        self.check_freq = check_freq
        self.memory_threshold = memory_threshold
        self.last_check_time = time.time()
        self.last_gc_time = time.time()

    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:
            memory_percent = psutil.virtual_memory().percent

            if memory_percent > self.memory_threshold:
                if self.verbose > 0:
                    print(f"\n[SAFETY] Memory: {memory_percent:.1f}% > {self.memory_threshold}%")
                    print("   Running emergency GC...")
                gc.collect()
                time.sleep(0.5)
                new_mem = psutil.virtual_memory().percent
                if self.verbose > 0:
                    print(f"   After cleanup: {new_mem:.1f}%")

                if new_mem > self.memory_threshold + 5:
                    if self.verbose > 0:
                        print("   WARNING: Memory still high!")

            current_time = time.time()
            if current_time - self.last_gc_time > 30:
                self.last_gc_time = current_time
                gc.collect()

            if current_time - self.last_check_time > 30:
                self.last_check_time = current_time
                if self.verbose > 0:
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    mem_used = psutil.virtual_memory().used / 1024**3
                    mem_total = psutil.virtual_memory().total / 1024**3
                    print(f"\n[STATUS] CPU: {cpu_percent:.1f}% | Memory: {mem_used:.2f}/{mem_total:.2f} GB")

        return True


class TimestepLogger(BaseCallback):
    """每50万步记录进度"""

    def __init__(self, log_interval=500000):
        super().__init__()
        self.log_interval = log_interval

    def _on_step(self) -> bool:
        if self.n_calls % self.log_interval == 0:
            elapsed = time.time() - self.model.start_time
            fps = self.n_calls / elapsed if elapsed > 0 else 0
            print(f"\n[PROGRESS] Steps: {self.n_calls:,} / {self.model._total_timesteps:,} | Time: {elapsed/60:.1f} min | FPS: {fps:.0f}")
        return True


def setup_safe_exit(model, env, eval_env):
    """设置安全退出处理"""
    def safe_exit(signum, frame):
        print("\n[SAFE EXIT] Saving model...")
        try:
            model.save("ppo_reach_enhanced_safe_exit")
            print("[SAFE EXIT] Model saved")
        except Exception as e:
            print(f"[SAFE EXIT] Save failed: {e}")
        try:
            env.close()
        except:
            pass
        try:
            eval_env.close()
        except:
            pass
        gc.collect()
        print("[SAFE EXIT] Cleanup complete")
        os._exit(0)

    signal.signal(signal.SIGINT, safe_exit)
    signal.signal(signal.SIGTERM, safe_exit)


if __name__ == "__main__":
    print("=" * 70)
    print("  Enhanced RobotReachEnv PPO Training")
    print("  集成仿真增强模块：领域随机化、通信延迟、执行器动力学、外部扰动")
    print("=" * 70)

    memory = psutil.virtual_memory()
    cpu_count = psutil.cpu_count(logical=True)

    print(f"\n[SYSTEM INFO]")
    print(f"   CPU Cores: {cpu_count}")
    print(f"   Total RAM: {memory.total / 1024**3:.2f} GB")
    print(f"   Available RAM: {memory.available / 1024**3:.2f} GB")

    # 训练配置 - 适配当前电脑配置
    n_envs = 4  # 减少并行环境数量，降低内存占用
    total_timesteps = 3_000_000  # 减少训练步数，加快收敛
    learning_rate = 3e-4
    n_steps = 2048
    batch_size = 256
    n_epochs = 10
    gamma = 0.99

    print(f"\n[TRAINING CONFIG]")
    print(f"   Parallel Environments: {n_envs}")
    print(f"   Total Steps: {total_timesteps:,}")
    print(f"   Learning Rate: {learning_rate}")
    print(f"   Device: CPU")

    print(f"\n[ENHANCEMENT MODULES]")
    print(f"   ✅ 领域随机化 (周期: 30s)")
    print(f"   ✅ 通信延迟仿真 (控制延迟: 3ms)")
    print(f"   ✅ 执行器动力学 (力矩限制: 50N·m)")
    print(f"   ✅ 外部扰动仿真 (周期性力: 2N)")
    print(f"   ✅ 传感器噪声 (高斯噪声: 0.5mm)")

    # 创建并行环境（Windows使用DummyVecEnv）
    from stable_baselines3.common.vec_env import DummyVecEnv
    print(f"\nCreating {n_envs} parallel environments (DummyVecEnv)...")
    try:
        env = DummyVecEnv([make_env(i) for i in range(n_envs)])
        env = VecMonitor(env)
        print(f"   Successfully created {n_envs} environments")
    except Exception as e:
        print(f"   ERROR: {e}")
        n_envs = 1
        print(f"   Falling back to {n_envs} environment...")
        env = DummyVecEnv([make_env(0)])
        env = VecMonitor(env)

    # 评估环境
    eval_env = DummyVecEnv([lambda: EnhancedRobotReachEnv(render_mode=None, max_steps=500)])
    eval_env = VecMonitor(eval_env)

    # Callbacks
    resource_callback = SafeResourceMonitor(check_freq=1000, memory_threshold=75, verbose=1)
    timestep_callback = TimestepLogger(log_interval=500000)

    eval_callback = EvalCallback(
        eval_env,
        eval_freq=50000,
        n_eval_episodes=20,
        best_model_save_path="./best_reach_enhanced/",
        log_path="./eval_logs_reach_enhanced/",
        deterministic=True,
        verbose=1
    )

    checkpoint_callback = CheckpointCallback(
        save_freq=100000,
        save_path="./checkpoints_reach_enhanced/",
        name_prefix="ppo_reach",
        verbose=1
    )

    # 初始化PPO模型
    print("\nInitializing PPO model (CPU-only)...")
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=learning_rate,
        n_steps=n_steps,
        batch_size=batch_size,
        n_epochs=n_epochs,
        gamma=gamma,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        vf_coef=0.5,
        max_grad_norm=0.5,
        verbose=1,
        tensorboard_log="./logs_reach_enhanced/",
        device="cpu"
    )

    model.start_time = time.time()

    print(f"\nModel Parameters: {sum(p.numel() for p in model.policy.parameters()):,}")
    print(f"\nStarting Training ({total_timesteps:,} steps)...")
    print("=" * 70)

    setup_safe_exit(model, env, eval_env)

    start_time = time.time()

    try:
        model.learn(
            total_timesteps=total_timesteps,
            callback=[resource_callback, timestep_callback, eval_callback, checkpoint_callback],
            progress_bar=True
        )

        elapsed = time.time() - start_time
        print(f"\n[SUCCESS] Training Completed!")
        print(f"   Total Time: {elapsed/60:.2f} minutes")
        print(f"   Average Speed: {total_timesteps/elapsed:.1f} steps/second")

        gc.collect()
        model.save("ppo_robot_reach_enhanced_final")
        print("   Model Saved: ppo_robot_reach_enhanced_final")

    except KeyboardInterrupt:
        print("\n\n[INTERRUPT] User interrupted training")
        gc.collect()
        model.save("ppo_robot_reach_enhanced_interrupted")
        print("   Model Saved: ppo_robot_reach_enhanced_interrupted")

    except Exception as e:
        print(f"\n\n[ERROR] Training failed: {e}")
        import traceback
        traceback.print_exc()
        try:
            gc.collect()
            model.save("ppo_robot_reach_enhanced_error")
            print("   Model Saved: ppo_robot_reach_enhanced_error")
        except Exception as save_err:
            print(f"   Save failed: {save_err}")

    finally:
        print("\n[CLEANUP] Closing environments...")
        try:
            env.close()
            print("   Training environments closed")
        except Exception as e:
            print(f"   Warning: {e}")

        try:
            eval_env.close()
            print("   Evaluation environment closed")
        except Exception as e:
            print(f"   Warning: {e}")

        gc.collect()

        memory = psutil.virtual_memory()
        print(f"\n[FINAL STATUS] Memory Usage: {memory.percent:.1f}%")
        print("=" * 70)

    # 测试阶段
    print("\n" + "=" * 70)
    print("  Testing Enhanced Training Results")
    print("=" * 70)

    try:
        test_env = EnhancedRobotReachEnv(render_mode=None, max_steps=500)
        test_model = PPO.load("ppo_robot_reach_enhanced_final", env=test_env, device="cpu")

        success_count = 0
        total_episodes = 50
        all_rewards = []
        all_distances = []

        print(f"\nRunning {total_episodes} test episodes...\n")

        for ep in range(total_episodes):
            obs, info = test_env.reset()
            episode_reward = 0

            for step in range(500):
                action, _ = test_model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = test_env.step(action)
                episode_reward += reward

                if terminated:
                    success_count += 1
                    all_rewards.append(episode_reward)
                    all_distances.append(info.get("distance", 0))
                    status = "[OK]"
                    break
                elif truncated:
                    all_rewards.append(episode_reward)
                    all_distances.append(info.get("distance", 999))
                    status = "[FAIL]"
                    break

            if (ep + 1) % 10 == 0:
                print(f"  Episode {ep+1:3d}: {status} | Steps: {step+1:3d} | Reward: {episode_reward:.2f}")

        test_env.close()

        print(f"\n[TEST RESULTS]")
        print(f"   Success Rate: {success_count}/{total_episodes} ({success_count/total_episodes*100:.1f}%)")
        if all_rewards:
            print(f"   Average Reward: {np.mean(all_rewards):.2f}")
        if success_count > 0:
            success_dists = [d for i, d in enumerate(all_distances) if d < 999]
            print(f"   Avg Success Distance: {np.mean(success_dists):.4f}")

    except Exception as e:
        print(f"[TEST ERROR] Testing failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("  Enhanced Training Complete")
    print("=" * 70)