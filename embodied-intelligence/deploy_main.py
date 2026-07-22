"""
部署适配主脚本（支持真实机械臂对接）
安全原则：低资源占用、异常保护、自动恢复、模式隔离
"""

import pybullet as p
import pybullet_data
import time
import math
import threading
import signal
import sys

from deployment_config import (
    CONTROL_PARAMS,
    VALIDATED_BOUNDS,
    SIMULATION_PARAMS,
    ROBOT_CONFIG,
    MONITOR_PARAMS
)
from gpu_accelerator import enable_gpu_acceleration, optimize_rendering
from realtime_monitor import ResourceMonitor, RobotMonitor
from performance_monitor import PerformanceMonitor
from deploy_logger import DeployLogger
from param_calibration import ParameterCalibrator
from real_robot_adapter import RobotAdapter
from sensor_noise import SensorNoiseSystem
from noise_config import SENSOR_NOISE_CONFIG
from collision_detector import CollisionDetector, ForceFeedback
from collision_config import COLLISION_CONFIG, OBSTACLE_CONFIG
from data_recorder import DataRecorder
from data_config import DATA_RECORDER_CONFIG
from robot_config import (
    ROBOT_MODE,
    REAL_ROBOT_CONFIG,
    JOINT_INDICES,
    JOINT_LIMITS,
    START_JOINT_POSITIONS,
    CONTROL_PARAMS as ROBOT_CONTROL_PARAMS
)
from domain_randomization import DomainRandomizationSystem
from latency_simulator import LatencySystem
from actuator_dynamics import ActuatorSystem
from disturbance_simulator import DisturbanceSystem

physicsClient = None
resource_monitor = None
robot_monitor = None
perf_monitor = None
logger = None
robot_adapter = None
noise_system = None
collision_detector = None
force_feedback = None
obstacle_ids = []
data_recorder = None
domain_randomizer = None
latency_system = None
actuator_system = None
disturbance_system = None
running = True

def signal_handler(sig, frame):
    global running
    print("\n[DEPLOY] 收到中断信号，正在安全退出...")
    running = False

signal.signal(signal.SIGINT, signal_handler)

def init_environment():
    global physicsClient, resource_monitor, robot_monitor, perf_monitor, logger, robot_adapter, noise_system, collision_detector, force_feedback, obstacle_ids, data_recorder, domain_randomizer, latency_system, actuator_system, disturbance_system

    logger = DeployLogger()
    logger.info(f"初始化环境... (模式: {ROBOT_MODE})")

    noise_system = SensorNoiseSystem(SENSOR_NOISE_CONFIG)
    logger.info(f"传感器噪声模型已加载 (启用: {noise_system.is_enabled()})")

    collision_detector = CollisionDetector(COLLISION_CONFIG)
    force_feedback = ForceFeedback(COLLISION_CONFIG)
    logger.info(f"碰撞检测系统已加载 (启用: {collision_detector.is_enabled()})")

    data_recorder = DataRecorder(DATA_RECORDER_CONFIG)
    logger.info(f"数据记录系统已加载 (启用: {data_recorder.is_enabled()})")

    domain_randomizer = DomainRandomizationSystem({
        "enabled": True,
        "domain_randomizer": {
            "enabled": True,
            "randomize_interval": 120.0,
            "friction_range": [0.4, 0.6],
            "damping_range": [0.02, 0.08],
            "mass_range": [0.95, 1.05],
            "gravity_range": [-9.85, -9.75]
        },
        "mass_randomizer": {"enabled": False},
        "friction_randomizer": {"enabled": False},
        "physics_distortion": {"enabled": False}
    })
    logger.info(f"领域随机化系统已加载 (启用: {domain_randomizer.is_enabled()})")

    latency_system = LatencySystem({
        "enabled": True,
        "latency_simulator": {"enabled": True, "mean_latency_ms": 10},
        "control_delay": {"enabled": True, "delay_ms": 8},
        "state_delay": {"enabled": True, "delay_ms": 5},
        "network_latency": {"enabled": True, "mean_rtt_ms": 15, "jitter_ms": 5}
    })
    logger.info(f"通信延迟系统已加载 (启用: {latency_system.is_enabled()})")

    actuator_system = ActuatorSystem({
        "enabled": True,
        "actuator_dynamics": {"enabled": True, "max_torque": 50.0, "max_velocity": 3.0},
        "motor_model": {"enabled": True},
        "joint_constraint": {"enabled": True, "max_force": 50.0}
    })
    logger.info(f"执行器动力学系统已加载 (启用: {actuator_system.is_enabled()})")

    disturbance_system = DisturbanceSystem({
        "enabled": True,
        "disturbance_simulator": {"enabled": True},
        "impact_simulator": {"enabled": True},
        "load_simulator": {"enabled": True}
    })
    logger.info(f"外部扰动系统已加载 (启用: {disturbance_system.is_enabled()})")

    robot_config = {
        "joint_indices": JOINT_INDICES,
        "joint_limits": JOINT_LIMITS,
        **REAL_ROBOT_CONFIG
    }
    robot_adapter = RobotAdapter(mode=ROBOT_MODE, config=robot_config)

    if not robot_adapter.initialize():
        logger.error("机器人适配器初始化失败")
        return None

    if ROBOT_MODE == "sim":
        physicsClient = p.connect(p.GUI)
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(*SIMULATION_PARAMS["gravity"])
        p.setRealTimeSimulation(0)

        enable_gpu_acceleration(physicsClient)
        optimize_rendering(physicsClient)

        plane_id = p.loadURDF("plane.urdf")

        table_col = p.createCollisionShape(p.GEOM_BOX, halfExtents=[0.5, 0.5, 0.02])
        table_vis = p.createVisualShape(p.GEOM_BOX, halfExtents=[0.5, 0.5, 0.02],
                                         rgbaColor=[0.6, 0.4, 0.2, 1])
        table_id = p.createMultiBody(baseMass=0, baseCollisionShapeIndex=table_col,
                                     baseVisualShapeIndex=table_vis, basePosition=[0.2, 0, -0.02])

        urdf_path = ROBOT_CONFIG["urdf_path"]
        robot_id = p.loadURDF(urdf_path, [0, 0, 0], useFixedBase=True)

        link_name_to_index = {}
        for i in range(p.getNumJoints(robot_id)):
            info = p.getJointInfo(robot_id, i)
            link_name = info[12].decode('utf-8')
            link_name_to_index[link_name] = i

        ee_index = link_name_to_index.get(ROBOT_CONFIG["ee_link"], -1)
        if ee_index == -1:
            ee_index = p.getNumJoints(robot_id) - 2

        robot_adapter.update_sim_params(robot_id, JOINT_INDICES, ee_index)

        joint_lower_limits = []
        joint_upper_limits = []
        joint_ranges = []
        joint_rest_poses = []

        for i in JOINT_INDICES:
            info = p.getJointInfo(robot_id, i)
            joint_lower_limits.append(info[8])
            joint_upper_limits.append(info[9])
            joint_ranges.append(info[9] - info[8])
            joint_rest_poses.append((info[8] + info[9]) / 2)

        resource_monitor = ResourceMonitor(interval=MONITOR_PARAMS["update_interval"])
        resource_monitor.start()

        perf_monitor = PerformanceMonitor(log_interval=MONITOR_PARAMS["log_interval"])
        perf_monitor.start()

        robot_monitor = RobotMonitor(robot_id, ee_index, JOINT_INDICES)

        obstacle_ids.append(table_id)

        for obs_name, obs_config in OBSTACLE_CONFIG.items():
            if obs_name == "table":
                continue
            if obs_config["type"] == "box":
                col = p.createCollisionShape(p.GEOM_BOX, halfExtents=obs_config["dimensions"])
                vis = p.createVisualShape(p.GEOM_BOX, halfExtents=obs_config["dimensions"],
                                         rgbaColor=obs_config["color"])
                obs_id = p.createMultiBody(baseMass=obs_config["mass"], baseCollisionShapeIndex=col,
                                          baseVisualShapeIndex=vis, basePosition=obs_config["position"])
            elif obs_config["type"] == "sphere":
                col = p.createCollisionShape(p.GEOM_SPHERE, radius=obs_config["radius"])
                vis = p.createVisualShape(p.GEOM_SPHERE, radius=obs_config["radius"],
                                         rgbaColor=obs_config["color"])
                obs_id = p.createMultiBody(baseMass=obs_config["mass"], baseCollisionShapeIndex=col,
                                          baseVisualShapeIndex=vis, basePosition=obs_config["position"])
            obstacle_ids.append(obs_id)
            logger.info(f"障碍物已创建: {obs_name}", position=obs_config["position"])

        collision_detector.start_monitoring(robot_id, obstacle_ids)
        logger.info(f"碰撞监控已启动 (障碍物数量: {len(obstacle_ids)})")

        data_recorder.start()
        logger.info("数据记录已启动")

        logger.info("仿真环境初始化完成", ee_link=ROBOT_CONFIG["ee_link"], ee_index=ee_index)

        return {
            "robot_id": robot_id,
            "ee_index": ee_index,
            "joint_indices": JOINT_INDICES,
            "joint_lower_limits": joint_lower_limits,
            "joint_upper_limits": joint_upper_limits,
            "joint_ranges": joint_ranges,
            "joint_rest_poses": joint_rest_poses,
        }
    else:
        resource_monitor = ResourceMonitor(interval=MONITOR_PARAMS["update_interval"])
        resource_monitor.start()

        perf_monitor = PerformanceMonitor(log_interval=MONITOR_PARAMS["log_interval"])
        perf_monitor.start()

        logger.info("真实机械臂环境初始化完成")
        return {"robot_id": None, "ee_index": 7, "joint_indices": JOINT_INDICES}

def compute_ik(config, target_pos):
    if ROBOT_MODE != "sim" or config["robot_id"] is None:
        return None

    ik_joints = p.calculateInverseKinematics(
        config["robot_id"],
        config["ee_index"],
        target_pos,
        targetOrientation=[0, 0, 0, 1],
        lowerLimits=config["joint_lower_limits"],
        upperLimits=config["joint_upper_limits"],
        jointRanges=config["joint_ranges"],
        restPoses=config["joint_rest_poses"],
        maxNumIterations=CONTROL_PARAMS["ik_max_iter"],
        residualThreshold=CONTROL_PARAMS["ik_threshold"]
    )
    return [ik_joints[idx] if idx < len(ik_joints) else 0.0 for idx in config["joint_indices"]]

def move_to_position(config, target_pos, steps=None):
    if ROBOT_MODE == "real":
        robot_adapter.move_cartesian(*target_pos, speed=0.5)
        time.sleep(0.2)
        current_pose = robot_adapter.get_ee_pose()
        return current_pose["position"]

    steps = steps if steps else CONTROL_PARAMS["move_speed"]
    target_joints = compute_ik(config, target_pos)
    if target_joints is None:
        return [0, 0, 0]

    for idx, joint_idx in enumerate(config["joint_indices"]):
        p.setJointMotorControl2(config["robot_id"], joint_idx, p.POSITION_CONTROL,
                               targetPosition=target_joints[idx], force=CONTROL_PARAMS["force"])
    for _ in range(steps):
        p.stepSimulation()
        time.sleep(0.001)
    
    link_state = p.getLinkState(config["robot_id"], config["ee_index"])
    actual_pos = link_state[0]
    
    if noise_system:
        actual_pos = noise_system.apply_ee_noise(actual_pos)
    
    return actual_pos

def converge_to_target(config, target_pos):
    if ROBOT_MODE == "real":
        error = robot_adapter.converge_to_target(
            target_pos,
            max_iter=ROBOT_CONTROL_PARAMS["convergence_iterations"],
            threshold=ROBOT_CONTROL_PARAMS["convergence_threshold"]
        )
        return error

    for _ in range(10):
        link_state = p.getLinkState(config["robot_id"], config["ee_index"])
        current_pos = link_state[0]
        
        if noise_system:
            current_pos = noise_system.apply_ee_noise(current_pos)
        
        error = math.sqrt(
            (current_pos[0] - target_pos[0])**2 +
            (current_pos[1] - target_pos[1])**2 +
            (current_pos[2] - target_pos[2])**2
        )
        if error < CONTROL_PARAMS["convergence_threshold"]:
            break
        target_joints = compute_ik(config, target_pos)
        if target_joints is None:
            break
        for idx, joint_idx in enumerate(config["joint_indices"]):
            p.setJointMotorControl2(config["robot_id"], joint_idx, p.POSITION_CONTROL,
                                   targetPosition=target_joints[idx], force=CONTROL_PARAMS["force"])
        for _ in range(CONTROL_PARAMS["convergence_steps"]):
            p.stepSimulation()
            time.sleep(0.001)

    return error

def reset_robot(config):
    if ROBOT_MODE == "real":
        robot_adapter.move_joints(START_JOINT_POSITIONS, speed=0.5)
        time.sleep(1.0)
        return

    for idx, joint_idx in enumerate(config["joint_indices"]):
        p.resetJointState(config["robot_id"], joint_idx, START_JOINT_POSITIONS[idx])
    for _ in range(50):
        p.stepSimulation()

def execute_task(config, target_pos):
    reset_robot(config)

    start_pos = [0.0, 0.0, 0.6]
    num_steps = 30
    trajectory = []
    for i in range(num_steps + 1):
        t = i / num_steps
        x = start_pos[0] + (target_pos[0] - start_pos[0]) * t
        y = start_pos[1] + (target_pos[1] - start_pos[1]) * t
        z = start_pos[2] + (target_pos[2] - start_pos[2]) * t
        trajectory.append([x, y, z])

    for target_point in trajectory:
        move_to_position(config, target_point)

    converge_to_target(config, target_pos)

    if ROBOT_MODE == "real":
        current_pose = robot_adapter.get_ee_pose()
        final_pos = current_pose["position"]
    else:
        link_state = p.getLinkState(config["robot_id"], config["ee_index"])
        final_pos = link_state[0]
        
        if noise_system:
            final_pos = noise_system.apply_ee_noise(final_pos)

    final_error = math.sqrt(
        (final_pos[0] - target_pos[0])**2 +
        (final_pos[1] - target_pos[1])**2 +
        (final_pos[2] - target_pos[2])**2
    )

    if robot_monitor:
        robot_monitor.log_error(final_error)
    return final_error

def run_calibration(config):
    if ROBOT_MODE != "sim" or config["robot_id"] is None:
        logger.info("跳过校准（真实机械臂模式）")
        return None

    calibrator = ParameterCalibrator(config["robot_id"], config["joint_indices"], config["ee_index"])
    results = calibrator.run_full_calibration()
    calibrator.save_results()
    return results

def deploy_loop(config):
    global running
    target_pos = [0.25, 0.0, 0.6]
    cycle_count = 0
    success_count = 0

    logger.info(f"开始部署循环... (模式: {ROBOT_MODE})", target_pos=target_pos, force=CONTROL_PARAMS["force"])

    while running:
        try:
            cycle_count += 1

            # 领域随机化 - 周期性执行
            if domain_randomizer and ROBOT_MODE == "sim":
                randomize_result = domain_randomizer.check_and_randomize(config["robot_id"], config["joint_indices"])
                if randomize_result:
                    logger.info(f"领域随机化已执行: {randomize_result}")

            # 应用通信延迟
            if latency_system:
                latency_system.apply_control_latency()

            error = execute_task(config, target_pos)

            # 应用外部扰动
            if disturbance_system and ROBOT_MODE == "sim":
                disturbances = disturbance_system.apply_disturbances(config["robot_id"], config["ee_index"])
                if disturbances:
                    for d in disturbances:
                        logger.info(f"扰动已应用: {d['type']}")

            passed = error < 0.02
            if passed:
                success_count += 1
                logger.success(f"循环 {cycle_count} 完成", error_mm=error*1000)
            else:
                logger.warn(f"循环 {cycle_count} 误差超限", error_mm=error*1000)

            stats = resource_monitor.get_stats()

            collision_stats = collision_detector.get_collision_stats() if collision_detector else {}
            if collision_detector:
                collision_detector.update()

            # 获取延迟统计
            latency_stats = latency_system.get_stats() if latency_system else {}
            actuator_stats = actuator_system.get_stats() if actuator_system else {}
            disturbance_stats = disturbance_system.get_stats() if disturbance_system else {}

            print(f"[DEPLOY] 循环 {cycle_count}: 误差 {error*1000:.2f}mm | "
                  f"CPU: {stats['cpu_current']:.1f}% | MEM: {stats['mem_current']:.1f}% | "
                  f"碰撞: {collision_stats.get('recent_collisions', 0)}")

            if data_recorder:
                if ROBOT_MODE == "real":
                    current_pose = robot_adapter.get_ee_pose()
                    current_pos = current_pose["position"]
                else:
                    link_state = p.getLinkState(config["robot_id"], config["ee_index"])
                    current_pos = link_state[0]

                data_recorder.record(
                    cycle=cycle_count,
                    target_pos=target_pos,
                    current_pos=current_pos,
                    error_mm=error * 1000,
                    cpu_percent=stats["cpu_current"],
                    mem_percent=stats["mem_current"],
                    collisions=collision_stats.get("recent_collisions", 0),
                    latency_ms=latency_stats.get("latency_simulator", {}).get("avg_latency_ms", 0),
                    disturbances=disturbance_stats.get("disturbance_simulator", {}).get("total_disturbances", 0)
                )

            if cycle_count % 10 == 0:
                perf_summary = perf_monitor.get_summary()
                if perf_summary:
                    logger.info("性能统计", avg_cpu=perf_summary["avg_cpu"],
                               avg_memory=perf_summary["avg_memory"])

                # 输出随机化和扰动统计
                if domain_randomizer:
                    dr_stats = domain_randomizer.get_stats()
                    logger.info("领域随机化统计", **dr_stats)
                if disturbance_system:
                    ds_stats = disturbance_system.get_stats()
                    logger.info("扰动统计", **ds_stats)

            time.sleep(0.5)

        except Exception as e:
            logger.error(f"部署循环异常: {e}")
            time.sleep(1)

    pass_rate = success_count / cycle_count * 100 if cycle_count > 0 else 0
    logger.info("部署循环结束", cycle_count=cycle_count, pass_rate=pass_rate)

    print(f"\n[DEPLOY] 部署循环结束")
    print(f"[DEPLOY] 总循环次数: {cycle_count}")
    print(f"[DEPLOY] 成功率: {pass_rate:.1f}%")

    if perf_monitor:
        perf_monitor.save_report()

def cleanup():
    global physicsClient, resource_monitor, perf_monitor, logger, robot_adapter, collision_detector, data_recorder, domain_randomizer, latency_system, actuator_system, disturbance_system

    print("\n[DEPLOY] 清理资源...")

    if logger:
        logger.close()

    if resource_monitor:
        resource_monitor.stop()

    if perf_monitor:
        perf_monitor.stop()

    if data_recorder:
        data_recorder.stop()
        report_path = data_recorder.generate_report()
        print(f"[DATA] 数据报告已生成: {report_path}")

    if collision_detector:
        collision_detector.stop_monitoring()

    if domain_randomizer:
        domain_randomizer.disable()
        print("[DR] 领域随机化系统已禁用")

    if latency_system:
        latency_system.disable()
        print("[LATENCY] 通信延迟系统已禁用")

    if actuator_system:
        actuator_system.reset()
        actuator_system.disable()
        print("[ACTUATOR] 执行器动力学系统已重置")

    if disturbance_system:
        disturbance_system.reset()
        disturbance_system.disable()
        print("[DISTURBANCE] 外部扰动系统已重置")

    if robot_adapter:
        robot_adapter.shutdown()

    if physicsClient is not None:
        try:
            p.disconnect(physicsClient)
        except:
            pass

    print("[DEPLOY] 资源清理完成")

if __name__ == "__main__":
    try:
        config = init_environment()
        if config is None:
            sys.exit(1)

        run_calibration(config)

        deploy_loop(config)
    finally:
        cleanup()
        sys.exit(0)
