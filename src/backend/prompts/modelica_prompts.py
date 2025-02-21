import os
from typing import Optional, List
from openai import AzureOpenAI
from ..db.vector_store import ModelicaVectorStore
from pathlib import Path
from ..config.settings import Settings
import ipdb

class ModelicaPrompts:
    def __init__(self, persist_directory: Optional[str] = None):
        """初始化ModelicaPrompts
        
        Args:
            persist_directory: 向量数据库持久化目录
        """
        self.examples = self._get_example_models()
        self.vector_store = ModelicaVectorStore(persist_directory)
        # 初始化时加载示例到向量数据库
        #ipdb.set_trace()
        self.vector_store.add_examples(self.examples)
        self.examples_dir = Path(__file__).parent.parent / 'modelica' / 'example'
        
        
        # 初始化Azure OpenAI客户端
        self.client = AzureOpenAI(
            api_key=Settings.AZURE_OPENAI_API_KEY,
            api_version="2023-05-15",
            azure_endpoint=Settings.AZURE_OPENAI_ENDPOINT
        )


    def read_mo_file(self, filepath: str) -> str:
        """读取 .mo 文件内容"""
        # 获取当前文件的目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建到 example 目录的路径
        example_dir = os.path.join(os.path.dirname(current_dir), "modelica", "example")
        # 构建完整的文件路径
        full_path = os.path.join(example_dir, filepath)
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 用三引号包裹内容
            return f'"""{content}"""'

    def _get_example_models(self) -> dict:
        """获取示例模型字典"""
        return {
            "空白模板": {
                "keywords": ["空白", "模板", "基础"],
                "description": "基础的空白Modelica模型模板",
                "code": ('""""""', '""""""'),  # 返回空元组供GPT生成
                "model_name": "EmptyModel"
            },
            "染缸温控": {
                "keywords": ["染缸", "温度控制", "PID", "热传导", "对流"],
                "description": "染缸温度PID控制系统，包含热传导和对流",
                "code": self.read_mo_file("DyeVatSimulation.mo"),
                "model_name": "DyeingVat"
            },
            "小球掉落": {
                "keywords": ["小球", "掉落", "重力", "自由落体", "运动"],
                "description": "小球自由落体运动仿真",
                "code": self.read_mo_file("FallingMarble.mo"),
                "model_name": "FallingMarble"
            }
        }

    def get_examples(self):
        """获取缓存的示例代码"""
        return self.examples
      
    def find_matching_example(self, prompt: str) -> str:
        """查找最匹配的示例代码"""
        try:
            matches = self.vector_store.search(
                query=prompt,
                similarity_threshold=0.5
            )
            return matches[0]["code"] if matches else self._fallback_matching(prompt)
        except Exception as e:
            print(f"示例匹配失败: {str(e)}")
            return self._fallback_matching(prompt)

    # def _get_embedding(self, text: str) -> Optional[List[float]]:
    #     """获取文本的embedding向量"""
    #     try:
    #         response = self.client.embeddings.create(
    #             input=text,
    #             model=Settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
    #         )
    #         return response.data[0].embedding if response.data else None
    #     except Exception as e:
    #         print(f"获取embedding失败: {str(e)}")
    #         return None

    def _cosine_similarity(self, vec1: list, vec2: list) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        return dot_product / (norm1 * norm2)

    def _fallback_matching(self, prompt: str) -> str:
        """简单的关键词匹配作为备用方案"""
        keywords = {
            'falling': 'FallingMarble.mo',
            'marble': 'FallingMarble.mo',
            'dye': 'DyeVatSimulation.mo',
            'vat': 'DyeVatSimulation.mo',
            'boiler': 'BoilerCombustion.mo',
            'combustion': 'BoilerCombustion.mo'
        }
        
        prompt = prompt.lower()
        for key, filename in keywords.items():
            if key in prompt:
                file_path = self.examples_dir / filename
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return f.read()
        return ''

    # def calculate_similarity(self, text1: str, text2: str) -> float:
    #     """计算两段文本的相似度
        
    #     Args:
    #         text1: 第一段文本
    #         text2: 第二段文本
            
    #     Returns:
    #         相似度分数 (0-1)
    #     """
    #     # 将文本转换为词集合
    #     words1 = set(text1.lower().split())
    #     words2 = set(text2.lower().split())
        
    #     # 计算交集和并集
    #     intersection = words1 & words2
    #     union = words1 | words2
        
    #     # 计算Jaccard相似度
    #     return len(intersection) / len(union) if union else 0







def get_modelica_examples() -> str:
    """获取Modelica示例代码"""
    return """示例 1 - 染缸PID温度控制仿真：
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
===================================
示例 2 - 小球掉落仿真：
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

"""

def get_system_prompt() -> str:
    """获取系统提示词"""
    return """你是一个Modelica专家，能够将自然语言描述转换为正确的Modelica仿真代码。
请遵循以下规则：
1. 确保生成的代码包含完整的模型定义，包括model关键字和end关键字
2. 添加适当的注释说明代码的功能和参数
3. 使用标准的Modelica库组件
4. 确保变量和参数有合适的单位和初始值
5. 代码要符合Modelica编码规范
6. 添加合适的仿真设置，如stopTime、numberOfIntervals等
7. 确保导入所需的Modelica标准库

以下是一个成功的Modelica模型示例，请参考这个示例的风格和结构：

{example}"""