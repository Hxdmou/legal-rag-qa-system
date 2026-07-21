"""
传感器噪声配置文件
可根据真实传感器特性调整参数
"""

SENSOR_NOISE_CONFIG = {
    "enabled": True,

    "joint_gaussian_std": 0.001,
    "joint_quantization_res": 0.001,
    "joint_drift_rate": 0.00001,

    "ee_gaussian_std": 0.0001,
    "ee_quantization_res": 0.0001,
    "ee_drift_rate": 0.000001,

    "force_gaussian_std": 0.1,
    "force_drift_rate": 0.0001,
    "force_max_drift": 0.5,

    "velocity_gaussian_std": 0.001,
    "velocity_quantization_res": 0.001,
}

NOISE_LEVELS = {
    "none": {
        "enabled": False,
        "joint_gaussian_std": 0,
        "joint_quantization_res": 0.0001,
        "joint_drift_rate": 0,
        "ee_gaussian_std": 0,
        "ee_quantization_res": 0.00001,
        "ee_drift_rate": 0,
        "force_gaussian_std": 0,
        "force_drift_rate": 0,
        "force_max_drift": 0,
        "velocity_gaussian_std": 0,
        "velocity_quantization_res": 0.0001,
    },

    "low": {
        "enabled": True,
        "joint_gaussian_std": 0.0005,
        "joint_quantization_res": 0.0005,
        "joint_drift_rate": 0.000005,
        "ee_gaussian_std": 0.00005,
        "ee_quantization_res": 0.00005,
        "ee_drift_rate": 0.0000005,
        "force_gaussian_std": 0.05,
        "force_drift_rate": 0.00005,
        "force_max_drift": 0.25,
        "velocity_gaussian_std": 0.0005,
        "velocity_quantization_res": 0.0005,
    },

    "medium": {
        "enabled": True,
        "joint_gaussian_std": 0.001,
        "joint_quantization_res": 0.001,
        "joint_drift_rate": 0.00001,
        "ee_gaussian_std": 0.0001,
        "ee_quantization_res": 0.0001,
        "ee_drift_rate": 0.000001,
        "force_gaussian_std": 0.1,
        "force_drift_rate": 0.0001,
        "force_max_drift": 0.5,
        "velocity_gaussian_std": 0.001,
        "velocity_quantization_res": 0.001,
    },

    "high": {
        "enabled": True,
        "joint_gaussian_std": 0.002,
        "joint_quantization_res": 0.002,
        "joint_drift_rate": 0.00002,
        "ee_gaussian_std": 0.0002,
        "ee_quantization_res": 0.0002,
        "ee_drift_rate": 0.000002,
        "force_gaussian_std": 0.2,
        "force_drift_rate": 0.0002,
        "force_max_drift": 1.0,
        "velocity_gaussian_std": 0.002,
        "velocity_quantization_res": 0.002,
    },
}
