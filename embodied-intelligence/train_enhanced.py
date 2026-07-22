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
from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor
from stable_baselines3.common.callbacks import (
    BaseCallback,
    EvalCallback,
    CheckpointCallback
)

from robot_reach_env_enhanced import RobotReachEnvEnhanced


def make_env(rank, seed=0):
    def _init():
        env = RobotReachEnvEnhanced(render_mode=None, max_steps=500)
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
    n_envs = 2
    total_timesteps = 2_000_000
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

    # 评估环境（关闭增强模块以测试基础性能）
    eval_env = DummyVecEnv([lambda: RobotReachEnvEnhanced(
        render_mode=None, max_steps=500, enable_enhancement=False
    )])
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

    # 测试阶段 - 50轮测试评估
    print("\n" + "=" * 70)
    print("  Testing Enhanced Training Results")
    print("=" * 70)

    try:
        test_env = RobotReachEnvEnhanced(render_mode=None, max_steps=500)
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