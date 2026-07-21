"""
部署适配参数固化配置
基于 v3 版本 100% 通过验证的参数
"""

CONTROL_PARAMS = {
    "force": 200.0,
    "move_speed": 15,
    "convergence_steps": 50,
    "convergence_threshold": 0.001,
    "ik_max_iter": 2000,
    "ik_threshold": 1e-6,
}

VALIDATED_BOUNDS = {
    "mass_offset": [-0.184, 0.186],
    "damping_offset": [-0.299, 0.293],
    "friction_coeff": [0, 0.0468],
    "delay_steps": [0, 5],
}

SIMULATION_PARAMS = {
    "gravity": [0, 0, -9.8],
    "num_solver_iterations": 200,
    "num_sub_steps": 2,
    "time_step": 1 / 240,
}

ROBOT_CONFIG = {
    "urdf_path": "franka_panda/panda.urdf",
    "ee_link": "panda_link8",
    "joint_indices": [0, 1, 2, 3, 4, 5, 6],
    "start_joint_positions": [0, -0.785, 0, -2.356, 0, 1.571, 0.785],
}

MONITOR_PARAMS = {
    "update_interval": 1.0,
    "log_interval": 5.0,
    "max_history": 100,
}
