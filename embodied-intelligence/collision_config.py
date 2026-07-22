"""
碰撞检测配置文件
可根据真实场景调整参数
"""

COLLISION_CONFIG = {
    "enabled": True,
    
    "safety_distance": 0.01,
    "warning_distance": 0.02,
    "check_interval": 0.01,
    "max_contacts": 100,
    
    "force_threshold": 10.0,
    "max_force": 100.0,
}

COLLISION_LEVELS = {
    "none": {
        "enabled": False,
        "safety_distance": 0.001,
        "warning_distance": 0.002,
        "force_threshold": 0,
        "max_force": 0,
    },

    "low": {
        "enabled": True,
        "safety_distance": 0.015,
        "warning_distance": 0.025,
        "force_threshold": 5.0,
        "max_force": 50.0,
    },

    "medium": {
        "enabled": True,
        "safety_distance": 0.01,
        "warning_distance": 0.02,
        "force_threshold": 10.0,
        "max_force": 100.0,
    },

    "high": {
        "enabled": True,
        "safety_distance": 0.005,
        "warning_distance": 0.01,
        "force_threshold": 20.0,
        "max_force": 150.0,
    },
}

OBSTACLE_CONFIG = {
    "table": {
        "name": "table",
        "type": "box",
        "dimensions": [0.5, 0.5, 0.02],
        "position": [0.2, 0, -0.02],
        "color": [0.6, 0.4, 0.2, 1],
        "mass": 0,
    },
}
