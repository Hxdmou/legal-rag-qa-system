"""
快速微调脚本 - 基于已有4.8M步模型，继续训练50万步达到100%
"""
import sys
import os
sys.stderr = open(os.devnull, 'w')

import time
import multiprocessing

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor
from robot_reach_env_optimized import RobotReachEnvOptimized

def make_env(rank, seed=0, max_steps=400):
    def _init():
        env = RobotReachEnvOptimized(render_mode=None, max_steps=max_steps)
        env.reset(seed=seed + rank)
        return env
    return _init

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    print("=" * 70)
    print("  Fine-Tuning: Load 4.8M checkpoint + 500K steps")
    print("  Target: 100% Success Rate in <10 minutes")
    print("=" * 70)

    n_envs = 32
    additional_steps = 500_000
    max_steps_per_episode = 400

    print(f"\n[CONFIG]")
    print(f"   Parallel Environments: {n_envs}")
    print(f"   Additional Steps: {additional_steps:,}")

    # 创建环境
    env = DummyVecEnv([make_env(i, max_steps=max_steps_per_episode) for i in range(n_envs)])
    env = VecMonitor(env)

    # 加载已有模型
    checkpoint_path = 'checkpoints_reach_enhanced/ppo_reach_4800000_steps'
    print(f"\nLoading checkpoint: {checkpoint_path}")
    model = PPO.load(checkpoint_path, env=env, device='cpu')
    
    current_steps = model.num_timesteps
    print(f"   Current: {current_steps:,} steps")
    print(f"   Target: {current_steps + additional_steps:,} steps")

    # 微调训练
    print(f"\nStarting Fine-Tuning...")
    start_time = time.time()

    model.learn(
        total_timesteps=current_steps + additional_steps,
        progress_bar=False
    )

    elapsed = time.time() - start_time
    fps = additional_steps / elapsed
    print(f"\n[SUCCESS] Fine-Tuning Completed!")
    print(f"   Time: {elapsed/60:.2f} minutes")
    print(f"   FPS: {fps:.1f}")

    model.save("ppo_robot_reach_final")
    print("   Model Saved: ppo_robot_reach_final")

    # 纯Gym API测试
    print("\n=== Running 50 Test Episodes ===")
    test_env = RobotReachEnvOptimized(render_mode=None, max_steps=500)
    test_env.curriculum_progress = 1.0
    test_env._update_curriculum_target_range()
    
    success_count = 0
    total_reward = 0.0
    
    for i in range(50):
        obs, info = test_env.reset()
        done = False
        episode_reward = 0.0
        steps = 0
        
        while not done:
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = test_env.step(action)
            episode_reward += reward
            steps += 1
            done = terminated or truncated
        
        total_reward += episode_reward
        success_count += 1 if terminated else 0
        
        if (i + 1) % 10 == 0:
            status = 'OK' if terminated else 'FAIL'
            print(f'  Episode {i+1:3d}: [{status}] | Steps: {steps:3d} | Reward: {episode_reward:.2f}')

    print(f'\n[TEST RESULTS]')
    print(f'Success Rate: {success_count}/50 ({success_count/50*100:.1f}%)')
    print(f'Average Reward: {total_reward/50:.2f}')
    print(f'FPS: {fps:.1f}')
