"""
课程学习训练脚本 - 渐进式引入增强模块
训练阶段：
Stage 1 (0-10%): 纯基础环境，无增强
Stage 2 (10-30%): 引入微弱领域随机化
Stage 3 (30-50%): 引入微弱执行器动力学
Stage 4 (50-70%): 引入微弱外部扰动
Stage 5 (70-90%): 所有增强模块强度增加
Stage 6 (90-100%): 所有增强模块最大强度
"""

import sys
import os

old_stderr = sys.stderr
sys.stderr = open(os.devnull, 'w')
os.environ['PYBULLET_DISABLE_WARNINGS'] = '1'

import time
import multiprocessing

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor
from stable_baselines3.common.callbacks import BaseCallback

from robot_reach_env_optimized import RobotReachEnvOptimized


class CurriculumCallback(BaseCallback):
    """课程学习回调：根据训练进度动态调整增强模块强度"""
    
    def __init__(self, total_timesteps):
        super().__init__()
        self.total_timesteps = total_timesteps
        self.start_time = time.time()
        self.last_update = 0
    
    def _on_step(self) -> bool:
        actual_steps = self.num_timesteps
        
        if actual_steps - self.last_update >= 100000:
            self.last_update = actual_steps
            progress = actual_steps / self.total_timesteps
            
            # 更新所有环境的课程学习进度
            for env_idx in range(self.training_env.num_envs):
                env = self.training_env.envs[env_idx]
                env.set_curriculum_progress(progress)
            
            elapsed = time.time() - self.start_time
            fps = actual_steps / elapsed if elapsed > 0 else 0
            remaining = (self.total_timesteps - actual_steps) / fps if fps > 0 else 0
            
            sys.stderr = old_stderr
            print(f"\n╔══════════════════════════════════════════════════════════════════╗", flush=True)
            print(f"║ [PROGRESS] {progress*100:6.2f}% | Steps: {actual_steps:,}/{self.total_timesteps:,}     ║", flush=True)
            print(f"║ [CURRICULUM] Progress: {progress:.2f}                          ║", flush=True)
            print(f"║ [FPS]      {fps:8.1f} | Elapsed: {elapsed/60:6.1f} min | Remaining: {remaining/60:6.1f} min ║", flush=True)
            print(f"╚══════════════════════════════════════════════════════════════════╝", flush=True)
            sys.stderr = open(os.devnull, 'w')
        return True


def make_env(rank, seed=0, max_steps=600):
    def _init():
        env = RobotReachEnvOptimized(render_mode=None, max_steps=max_steps)
        env.set_curriculum_progress(0.0)
        env.reset(seed=seed + rank)
        return env
    return _init


if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    sys.stderr = old_stderr
    print("=" * 70, flush=True)
    print("  CURRICULUM LEARNING TRAINING", flush=True)
    print("=" * 70, flush=True)

    n_envs = 32
    total_timesteps = 5_000_000

    print(f"\n[CONFIG]", flush=True)
    print(f"   Parallel Environments: {n_envs}", flush=True)
    print(f"   Total Steps: {total_timesteps:,}", flush=True)
    print(f"\n[CURRICULUM STAGES]", flush=True)
    print(f"   Stage 1 (0-10%):    Pure base environment", flush=True)
    print(f"   Stage 2 (10-30%):   Weak domain randomization", flush=True)
    print(f"   Stage 3 (30-50%):   Weak actuator dynamics", flush=True)
    print(f"   Stage 4 (50-70%):   Weak external disturbance", flush=True)
    print(f"   Stage 5 (70-90%):   Increasing all enhancements", flush=True)
    print(f"   Stage 6 (90-100%):  Max enhancement intensity", flush=True)

    print(f"\nCreating {n_envs} parallel environments...", flush=True)
    sys.stderr = open(os.devnull, 'w')
    
    env = DummyVecEnv([make_env(i, max_steps=600) for i in range(n_envs)])
    env = VecMonitor(env)

    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        n_steps=4096,
        batch_size=1024,
        n_epochs=3,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.005,
        vf_coef=0.5,
        max_grad_norm=0.5,
        verbose=0,
        device="cpu",
        policy_kwargs={"net_arch": [256, 256]}
    )

    sys.stderr = old_stderr
    print(f"\nStarting Curriculum Training...", flush=True)
    print(f"   [Target] FPS: 6000+ | Success: 100% | Reward: Maximize", flush=True)
    start_time = time.time()
    sys.stderr = open(os.devnull, 'w')
    
    model.learn(
        total_timesteps=total_timesteps,
        callback=[CurriculumCallback(total_timesteps)],
        progress_bar=False
    )
    
    elapsed = time.time() - start_time
    fps = total_timesteps / elapsed
    
    sys.stderr = old_stderr
    print(f"\n╔══════════════════════════════════════════════════════════════════╗", flush=True)
    print(f"║ [SUCCESS] Curriculum Training Completed!                       ║", flush=True)
    print(f"║   Time: {elapsed/60:.2f} minutes                             ║", flush=True)
    print(f"║   FPS: {fps:.1f}                                             ║", flush=True)
    print(f"╚══════════════════════════════════════════════════════════════════╝", flush=True)
    
    model.save("ppo_robot_reach_curriculum")
    print("   Model Saved: ppo_robot_reach_curriculum", flush=True)

    # 测试1：基础环境测试（无增强）
    print("\n=== Test 1: Base Environment (No Enhancement) ===", flush=True)
    sys.stderr = open(os.devnull, 'w')
    
    test_env = RobotReachEnvOptimized(render_mode=None, max_steps=600)
    test_env.set_curriculum_progress(0.0)
    
    success_count = 0
    total_reward = 0.0
    
    for i in range(50):
        obs, info = test_env.reset()
        done = False
        episode_reward = 0.0
        
        while not done:
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = test_env.step(action)
            episode_reward += reward
            done = terminated or truncated
        
        total_reward += episode_reward
        success_count += 1 if terminated else 0
    
    avg_reward = total_reward / 50
    success_rate = success_count / 50 * 100
    
    sys.stderr = old_stderr
    print(f'\n╔══════════════════════════════════════════════════════════════════╗', flush=True)
    print(f'║ [TEST 1: BASE ENVIRONMENT]                                    ║', flush=True)
    print(f'╠══════════════════════════════════════════════════════════════════╣', flush=True)
    print(f'║ Success Rate: {success_count}/50 ({success_rate:.1f}%)          ║', flush=True)
    print(f'║ Average Reward: {avg_reward:.2f}                              ║', flush=True)
    print(f'╚══════════════════════════════════════════════════════════════════╝', flush=True)

    # 测试2：增强环境测试（最大强度）
    print("\n=== Test 2: Enhanced Environment (Max Intensity) ===", flush=True)
    sys.stderr = open(os.devnull, 'w')
    
    test_env2 = RobotReachEnvOptimized(render_mode=None, max_steps=600)
    test_env2.set_curriculum_progress(1.0)
    
    success_count2 = 0
    total_reward2 = 0.0
    
    for i in range(50):
        obs, info = test_env2.reset()
        done = False
        episode_reward = 0.0
        
        while not done:
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = test_env2.step(action)
            episode_reward += reward
            done = terminated or truncated
        
        total_reward2 += episode_reward
        success_count2 += 1 if terminated else 0
    
    avg_reward2 = total_reward2 / 50
    success_rate2 = success_count2 / 50 * 100
    
    sys.stderr = old_stderr
    print(f'\n╔══════════════════════════════════════════════════════════════════╗', flush=True)
    print(f'║ [TEST 2: ENHANCED ENVIRONMENT]                                ║', flush=True)
    print(f'╠══════════════════════════════════════════════════════════════════╣', flush=True)
    print(f'║ Success Rate: {success_count2}/50 ({success_rate2:.1f}%)        ║', flush=True)
    print(f'║ Average Reward: {avg_reward2:.2f}                            ║', flush=True)
    print(f'╚══════════════════════════════════════════════════════════════════╝', flush=True)

    # 最终评估
    fps_ok = fps >= 6000
    success_ok_base = success_rate >= 100.0
    success_ok_enhanced = success_rate2 >= 90.0
    
    print(f'\n╔══════════════════════════════════════════════════════════════════╗', flush=True)
    print(f'║ [FINAL EVALUATION]                                            ║', flush=True)
    print(f'╠══════════════════════════════════════════════════════════════════╣', flush=True)
    print(f'║ FPS: {fps:.1f} {"OK" if fps_ok else "FAIL"} (Target: 6000+)      ║', flush=True)
    print(f'║ Base Success: {success_rate:.1f}% {"OK" if success_ok_base else "FAIL"} (Target: 100%) ║', flush=True)
    print(f'║ Enhanced Success: {success_rate2:.1f}% {"OK" if success_ok_enhanced else "FAIL"} (Target: 90%) ║', flush=True)
    print(f'╚══════════════════════════════════════════════════════════════════╝', flush=True)
    
    if fps_ok and success_ok_base and success_ok_enhanced:
        print("[PASS] ALL TARGETS ACHIEVED!", flush=True)
    else:
        print("[PARTIAL] Some targets not fully achieved", flush=True)
