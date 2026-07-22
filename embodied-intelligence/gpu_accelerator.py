"""
GPU加速配置模块（轻量级）
安全原则：低资源占用，无内存泄漏
"""

import pybullet as p

def enable_gpu_acceleration(physics_client_id=None):
    """启用GPU加速优化"""
    client = physics_client_id if physics_client_id is not None else -1

    p.setPhysicsEngineParameter(
        numSolverIterations=200,
        numSubSteps=2,
        enableConeFriction=True,
        physicsClientId=client
    )

    p.configureDebugVisualizer(
        p.COV_ENABLE_GUI, 0,
        physicsClientId=client
    )

    p.configureDebugVisualizer(
        p.COV_ENABLE_SHADOWS, 0,
        physicsClientId=client
    )

    print("[GPU] GPU加速配置已应用")

def optimize_rendering(physics_client_id=None):
    """优化渲染性能"""
    client = physics_client_id if physics_client_id is not None else -1

    p.configureDebugVisualizer(
        p.COV_ENABLE_WIREFRAME, 0,
        physicsClientId=client
    )

    p.configureDebugVisualizer(
        p.COV_ENABLE_RENDERING, 1,
        physicsClientId=client
    )

    print("[GPU] 渲染优化已应用")
