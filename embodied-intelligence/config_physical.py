"""
物理因素深化配置文件
"""

# ================== 机械臂类型 ==================
USE_KUKA = False

# ================== 目标位置 ==================
TARGET_END_POS = [0.25, 0.0, 0.6]

# ================== 物理因素开关 ==================
ENABLE_FRICTION = True          # 启用关节摩擦力
ENABLE_SENSOR_NOISE = True      # 启用传感器噪声
ENABLE_COMM_DELAY = True        # 启用通信延迟
ENABLE_GRAVITY_COMP = True      # 启用重力补偿验证

# ================== 摩擦力参数 ==================
FRICTION_COEFF = 0.05           # 库仑摩擦系数
VISCOSITY_COEFF = 0.01          # 粘性摩擦系数

# ================== 传感器噪声参数 ==================
POSITION_NOISE_STD = 0.0005     # 位置噪声标准差（米）
VELOCITY_NOISE_STD = 0.001      # 速度噪声标准差（米/秒）

# ================== 通信延迟参数 ==================
COMM_DELAY_STEPS = 3            # 固定延迟步数
USE_RANDOM_DELAY = True         # 是否使用随机延迟
RANDOM_DELAY_MAX = 5            # 随机延迟最大步数

# ================== 运动参数 ==================
MOVEMENT_SPEED = 5              # 每点仿真步数
SIMULATION_STEPS = 500          # 总仿真步数
