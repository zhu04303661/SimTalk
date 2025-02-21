// 非结构化 Modelica 文件示例
model FallingMarble
  // 常量参数
  parameter Real g = 9.81 "重力加速度 (m/s²)";
  parameter Real radius = 0.01 "弹珠半径 (m)";
  parameter Real mass = 0.1 "弹珠质量 (kg)";
  
  // 变量定义
  Real height(start = 10) "距离地面高度 (m)";
  Real velocity "下落速度 (m/s)";
  Real acceleration "瞬时加速度 (m/s²)";

equation
  // 运动学方程
  der(height) = -velocity;        // 高度变化率
  der(velocity) = acceleration;   // 速度变化率
  acceleration = g;               // 自由落体加速度
  
  // 仿真参数注解
  annotation(
    experiment(
      StopTime=SimulationSettings.stopTime,
      Interval=SimulationSettings.interval,
      __Dymola_Algorithm=SimulationSettings.algorithmType
    )
  );
end FallingMarble;

block SimulationSettings
  // 全局仿真参数配置
  constant Real stopTime = 15 "仿真持续时间 (s)";
  constant Real interval = 0.01 "存储间隔 (s)";
  constant String algorithmType = "Dassl" "积分算法类型";
  
  // 通用物理常量（可扩展）
  constant Real earthGravity = 9.81 "地球重力 (m/s²)";
  constant Real airDensity = 1.225 "空气密度 (kg/m³)";
end SimulationSettings;
