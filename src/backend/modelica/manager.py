from typing import Dict, Any, Optional
import os
import subprocess
import tempfile
import logging
import pandas as pd
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

class OpenModelicaManager:
    """OpenModelica功能管理类"""
    
    def __init__(self):
        self.omc = None
        self.is_available = False
        self.status_message = ""
        self._check_installation()
        if self.is_available:
            self._initialize_session()

    def simulate_model(self, modelica_code: str, model_name: str) -> Dict[str, Any]:
        """执行Modelica模型仿真"""
        if not self.is_available:
            return self._create_error_response('OpenModelica未安装，仿真功能不可用')

        temp_dir = None
        try:
            temp_dir = self._setup_simulation_environment(modelica_code, model_name)
            result = self._run_simulation(temp_dir, model_name)
            return self._process_simulation_result(result, temp_dir, model_name)
        except Exception as e:
            logger.error(f"仿真过程出错: {e}")
            return self._create_error_response(str(e))
        finally:
            self._cleanup(temp_dir)

    # ... 其他方法保持不变，但移动到这个文件中 