from typing import Tuple
import os
from openai import AzureOpenAI
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
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version="2023-05-15",
            azure_endpoint=endpoint
        )
        self.deployment_name = deployment_name

    # ... 其他方法移动到这个文件中 