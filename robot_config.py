"""
机械臂配置文件
支持仿真模式和真实模式配置
"""

ROBOT_MODE = "sim"

REAL_ROBOT_CONFIG = {
    "host": "192.168.3.100",
    "port": 8080,
    "timeout": 5.0,
}

JOINT_INDICES = [0, 1, 2, 3, 4, 5, 6]

JOINT_LIMITS = {
    "lower": [-2.967, -1.832, -2.967, -3.141, -2.967, -0.087, -2.967],
    "upper": [2.967, 1.832, 2.967, -0.069, 2.967, 3.822, 2.967],
}

EE_LINK = "panda_link8"

START_JOINT_POSITIONS = [0, -0.785, 0, -2.356, 0, 1.571, 0.785]

CONTROL_PARAMS = {
    "force": 200.0,
    "speed": 1.0,
    "convergence_threshold": 0.001,
    "convergence_iterations": 10,
}

SAFETY_PARAMS = {
    "max_speed": 3.0,
    "max_force": 100.0,
    "workspace_radius": 0.8,
}
