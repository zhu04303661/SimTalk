model DyeVatSimulation
  // 导入必要的模型库
  import Modelica.Thermal.HeatTransfer.*;
  import Modelica.Blocks.*;
  import Modelica.Blocks.Sources.*;

  // 组件声明（使用完整路径）
  Modelica.Thermal.HeatTransfer.Components.HeatCapacitor vat(
    C=5000, 
    T(start=293.15, fixed=true))
    "染缸热容（假设为金属材质）";

  Modelica.Thermal.HeatTransfer.Components.ThermalConductor wall(
    G=10)
    "缸壁热传导（与环境的热交换）";

  Modelica.Thermal.HeatTransfer.Components.Convection convection
    "搅拌增强的热对流";

  Modelica.Thermal.HeatTransfer.Sources.FixedTemperature environment(
    T=293.15)
    "环境温度(20°C)";

  Modelica.Thermal.HeatTransfer.Sources.PrescribedHeatFlow heater
    "电加热元件";

  Modelica.Blocks.Continuous.LimPID PID(
    k=20,
    Ti=120,
    Td=10,
    yMax=5000,
    yMin=0)
    "PID温度控制器";

  Modelica.Blocks.Sources.RealExpression setTemp(
    y=273.15 + 80)
    "设定温度(80°C)";
  
  Real actualTemp "反馈温度值";

  Modelica.Blocks.Sources.Step stirSpeed(
    height=0.5,
    offset=0.5,
    startTime=300)
    "搅拌速度变化（影响对流系数）";

equation 
  // 系统连接
  connect(wall.port_a, vat.port);
  connect(wall.port_b, environment.port);
  connect(heater.port, vat.port);
  connect(PID.u_s, setTemp.y);
  connect(PID.u_m, actualTemp);
  connect(PID.y, heater.Q_flow);
  connect(vat.port, convection.solid);
  connect(convection.fluid, environment.port);
  // Removed connect(stirSpeed.y, convection.Gc);

  // 实际温度反馈
  actualTemp = vat.T;

  // 对流系数与搅拌速度的关系
  convection.Gc = 5 + 20*stirSpeed.y;

end DyeVatSimulation;