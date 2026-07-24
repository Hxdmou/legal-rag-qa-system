"""
纯Gym API测试脚本 - 不使用VecEnv，避免自动reset干扰
"""
import sys
import os
sys.stderr = open(os.devnull, 'w')

import numpy as np
from stable_baselines3 import PPO
from robot_reach_env_optimized import RobotReachEnvOptimized

# 创建单个环境（纯Gym API）
print("Creating single Gym environment...")
env = RobotReachEnvOptimized(render_mode=None, max_steps=500)
env.curriculum_progress = 1.0
env._update_curriculum_target_range()

# 加载模型（不传递env参数）
print("Loading model...")
model = PPO.load('checkpoints_reach_enhanced/ppo_reach_4800000_steps', device='cpu')

print("\nRunning 50 test episodes (Pure Gym API)...")
success_count = 0
total_reward = 0.0

for i in range(50):
    obs, info = env.reset()  # Gym API返回(obs, info)
    done = False
    episode_reward = 0.0
    steps = 0
    
    while not done:
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)  # Gym API返回5个值
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
