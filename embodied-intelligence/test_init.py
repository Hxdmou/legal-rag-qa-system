import sys
import os
os.environ['PYBULLET_DISABLE_WARNINGS'] = '1'
sys.stderr = open(os.devnull, 'w')

import time

start = time.time()
from robot_reach_env_optimized import RobotReachEnvOptimized
print(f"Import time: {time.time() - start:.2f}s")

# Test 16 environments
start = time.time()
envs = []
for i in range(16):
    env = RobotReachEnvOptimized(render_mode=None)
    envs.append(env)
    print(f"Env {i+1}/16 created")
print(f"16 Env init time: {time.time() - start:.2f}s")

start = time.time()
for i, env in enumerate(envs):
    obs, info = env.reset()
    print(f"Env {i+1}/16 reset")
print(f"16 Reset time: {time.time() - start:.2f}s")

start = time.time()
for _ in range(100):
    for env in envs:
        obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
print(f"16 envs x 100 steps time: {time.time() - start:.2f}s, FPS: {1600 / (time.time() - start):.1f}")
