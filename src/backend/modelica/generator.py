from typing import Tuple, Optional
import os
import re
from ..providers.azure_openai import azure_openai
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

class ModelicaCodeGenerator:
    """Modelica代码生成器类"""
    
    def __init__(self, api_key: str, endpoint: str, deployment_name: str):
        self.client = azure_openai
        self.deployment_name = deployment_name
        self.system_prompt = self._get_system_prompt()

    def generate_code(self, prompt: str) -> Tuple[str, str]:
        """生成Modelica代码"""
        try:
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ]
            
            modelica_code = self.client.generate_completion(messages)
            if not modelica_code:
                raise ValueError("代码生成失败")
                
            model_name = self._extract_model_name(modelica_code)
            return modelica_code, model_name
            
        except Exception as e:
            print(f"代码生成失败: {str(e)}")
            raise

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个Modelica专家，能够将自然语言描述转换为正确的Modelica仿真代码。
请遵循以下规则：
1. 确保生成的代码包含完整的模型定义，包括model关键字和end关键字
2. 添加适当的注释说明代码的功能和参数
3. 使用标准的Modelica库组件
4. 确保变量和参数有合适的单位和初始值
5. 代码要符合Modelica编码规范
6. 添加合适的仿真设置，如stopTime、numberOfIntervals等
7. 确保导入所需的Modelica标准库"""

    def _extract_model_name(self, modelica_code: str) -> str:
        """从代码中提取模型名称"""
        if not isinstance(modelica_code, str):
            raise ValueError("模型代码必须是字符串类型")
            
        model_match = re.search(r'model\s+(\w+)', modelica_code)
        if not model_match:
            raise ValueError('无法从生成的代码中识别模型名称')
        return model_match.group(1)

    # ... 其他方法移动到这个文件中 