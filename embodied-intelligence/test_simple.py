import sys
import os
import traceback

# 抑制PyBullet警告
sys.stderr = open(os.devnull, 'w')

from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
from robot_reach_env_optimized import RobotReachEnvOptimized

def test_model(model_path):
    print(f"\n=== Testing: {model_path} ===")
    try:
        # 创建16个并行环境（与训练时一致）
        def make_env():
            env = RobotReachEnvOptimized(render_mode=None, max_steps=500)
            env.curriculum_progress = 1.0
            env._update_curriculum_target_range()
            return Monitor(env)
        
        test_env = DummyVecEnv([make_env for _ in range(16)])

        model = PPO.load(model_path, env=test_env, device='cpu')

        success_count = 0
        total_reward = 0.0

        for i in range(50):
            obs = test_env.reset()
            done = False
            episode_reward = 0.0
            steps = 0
            
            while not done:
                action, _states = model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated = test_env.step(action)
                episode_reward += reward[0]
                steps += 1
                done = terminated[0] or truncated[0]
            
            total_reward += episode_reward
            success_count += 1 if terminated[0] else 0
            
            if (i + 1) % 10 == 0:
                status = 'OK' if terminated[0] else 'FAIL'
                print(f'  Episode {i+1:3d}: [{status}] | Steps: {steps:3d} | Reward: {episode_reward:.2f}')

        print(f'\n[TEST RESULTS]')
        print(f'Success Rate: {success_count}/50 ({success_count/50*100:.1f}%)')
        print(f'Average Reward: {total_reward/50:.2f}')
        
        return success_count, total_reward
        
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
        return 0, 0.0

# 测试不同的模型
models = [
    'checkpoints_reach_enhanced/ppo_reach_4000000_steps',
    'checkpoints_reach_enhanced/ppo_reach_4800000_steps',
    'ppo_robot_reach_enhanced_final'
]

for model_path in models:
    test_model(model_path)
