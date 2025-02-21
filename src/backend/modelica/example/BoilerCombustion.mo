model BoilerCombustion
  // 导入标准 Modelica 库
  import Modelica;
  import Modelica.Fluid.System;
  import Modelica.Fluid.Machines;
  import Modelica.Fluid.Sources;
  import Modelica.Fluid.Vessels;
  import Modelica.Fluid.Pipes;
  import Modelica.Media.Air;
  import Modelica.Thermal.HeatTransfer.Components;

  // 参数
  parameter Real fuelFlowRate = 1.0 "燃料流速（kg/s）";
  parameter Real airFlowRate = 10.0 "空气流速（kg/s）";
  parameter Real heatCapacityFuel = 42000 "燃料热容（J/kg）";
  parameter Real ambientTemperature = 293.15 "环境温度（K）";

  // 流体源
  Modelica.Fluid.Sources.Boundary_pT fuelSource(p = 1e5, T = ambientTemperature) "燃料源";
  Modelica.Fluid.Sources.Boundary_pT airSource(p = 1e5, T = ambientTemperature) "空气源";

  // 流体汇
  Modelica.Fluid.Sources.FixedBoundary ambient(p = 1e5) "环境";

  // 空气和燃料的混合器
  Modelica.Fluid.Vessels.MixingVolume combustionChamber(
    V = 1, use_C_start = true, C_start = {fuelFlowRate, airFlowRate},
    T_start = {ambientTemperature, ambientTemperature}) "燃烧室";

  // 换热器
  Modelica.Thermal.HeatTransfer.Components.HeatCapacitor heatExchanger(C = 1e4, T0 = ambientTemperature) "换热器";

  // 流体连接
  Modelica.Fluid.Pipes.StaticPipe pipe1(diameter = 0.1, length = 1) "从燃料源到燃烧室的管道";
  Modelica.Fluid.Pipes.StaticPipe pipe2(diameter = 0.1, length = 1) "从空气源到燃烧室的管道";
  Modelica.Fluid.Pipes.StaticPipe pipe3(diameter = 0.1, length = 1) "从燃烧室到环境的管道";

  // 燃烧过程的方程式
  equation
    // 燃料和空气在燃烧室中混合
    fuelSource.m_flow = fuelFlowRate;
    airSource.m_flow = airFlowRate;

    // 能量平衡方程
    combustionChamber.Q_flow[1] = fuelFlowRate * heatCapacityFuel;

    // 向换热器的热传递
    heatExchanger.Q_flow = combustionChamber.Q_flow[1];

  // 连接
  connect(fuelSource.ports[1], pipe1.port_a) "连接燃料源到管道";
  connect(pipe1.port_b, combustionChamber.ports[1]) "连接管道到燃烧室";

  connect(airSource.ports[1], pipe2.port_a) "连接空气源到管道";
  connect(pipe2.port_b, combustionChamber.ports[2]) "连接管道到燃烧室";

  connect(combustionChamber.ports[3], pipe3.port_a) "连接燃烧室到管道";
  connect(pipe3.port_b, ambient.ports[1]) "连接管道到环境";

  // 连接燃烧室到换热器
  connect(combustionChamber.ports[4], heatExchanger.port) "连接燃烧室到换热器";

  annotation (
    experiment(
      StopTime = 100,
      NumberOfIntervals = 500,
      Tolerance = 1e-6,
      Interval = 0.2));
end BoilerCombustion;
