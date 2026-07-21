"""
数据记录配置文件
可根据需求调整参数
"""

DATA_RECORDER_CONFIG = {
    "enabled": True,
    "record_interval": 0.1,
    "max_file_size": 10 * 1024 * 1024,
    "max_files": 5,
    "data_dir": "data",
}

RECORD_LEVELS = {
    "none": {
        "enabled": False,
        "record_interval": 1.0,
    },

    "minimal": {
        "enabled": True,
        "record_interval": 1.0,
        "max_file_size": 5 * 1024 * 1024,
        "max_files": 3,
    },

    "standard": {
        "enabled": True,
        "record_interval": 0.1,
        "max_file_size": 10 * 1024 * 1024,
        "max_files": 5,
    },

    "detailed": {
        "enabled": True,
        "record_interval": 0.01,
        "max_file_size": 20 * 1024 * 1024,
        "max_files": 10,
    },
}
