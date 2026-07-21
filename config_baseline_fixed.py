"""
基线精度测试配置文件（修正版）
"""

USE_KUKA = False
TARGET_END_POS = [0.25, 0.0, 0.6]
NUM_TRAJECTORY_POINTS = 30
MOVE_SPEED = 15                 # 增加步数，确保充分收敛
CONTROL_FORCE = 120.0           # 修正3：提高控制力
VERBOSE = True
