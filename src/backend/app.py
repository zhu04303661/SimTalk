from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import os
import tempfile
import sys
import subprocess
import json
import re
import logging
from typing import Dict, Tuple, Optional, Any
from openai import AzureOpenAI

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenModelicaManager:
    """OpenModelica功能管理类"""
    
    def __init__(self):
        self.omc = None
        self.is_available = False
        self.status_message = ""
        self._check_installation()
        if self.is_available:
            self._initialize_session()

    def _check_installation(self) -> None:
        """检查OpenModelica是否正确安装"""
        try:
            # 首先检查并设置OPENMODELICAHOME环境变量
            if 'OPENMODELICAHOME' not in os.environ:
                possible_paths = [
                    '/Applications/OpenModelica.app/Contents/Resources',
                    '/opt/openmodelica',
                ]
                
                for base_path in possible_paths:
                    omc_path = os.path.join(base_path, 'bin', 'omc')
                    if self._is_valid_omc_path(omc_path):
                        self._set_environment_variables(base_path)
                        self.is_available = True
                        self.status_message = f"已找到OpenModelica: {omc_path}"
                        return
            
            # 如果环境变量已设置，验证其有效性
            elif self._validate_openmodelica_home():
                self.is_available = True
                self.status_message = f"使用已配置的OpenModelica: {os.environ['OPENMODELICAHOME']}"
                return
            
            # 最后尝试在PATH中查找
            omc_path = self._find_omc_in_path()
            if omc_path:
                base_path = os.path.dirname(os.path.dirname(omc_path))
                self._set_environment_variables(base_path)
                self.is_available = True
                self.status_message = f"在PATH中找到OpenModelica: {omc_path}"
                return
            
            self.status_message = "OpenModelica未安装或配置不正确"
            
        except Exception as e:
            self.status_message = str(e)
            logger.error(f"检查OpenModelica安装时出错: {e}")

    def _validate_openmodelica_home(self) -> bool:
        """验证OPENMODELICAHOME环境变量的有效性"""
        try:
            home = os.environ['OPENMODELICAHOME']
            omc_path = os.path.join(home, 'bin', 'omc')
            return self._is_valid_omc_path(omc_path)
        except Exception:
            return False

    def _set_environment_variables(self, base_path: str) -> None:
        """设置OpenModelica相关的环境变量"""
        os.environ['OPENMODELICAHOME'] = base_path
        bin_path = os.path.join(base_path, 'bin')
        
        # 确保bin路径在PATH中
        if bin_path not in os.environ['PATH']:
            os.environ['PATH'] = f"{bin_path}:{os.environ['PATH']}"
        
        # 设置其他必要的环境变量
        os.environ['OPENMODELICALIBRARY'] = os.path.join(base_path, 'lib', 'omlibrary')
        os.environ['MODELICAUSERCFLAGS'] = f"-L{os.path.join(base_path, 'lib', 'omc')} -L{os.path.join(base_path, 'lib')}"

    def _is_valid_omc_path(self, path: str) -> bool:
        """检查给定路径是否为有效的OpenModelica可执行文件"""
        return os.path.exists(path) and os.access(path, os.X_OK)

    def _find_omc_in_path(self) -> Optional[str]:
        """在系统路径中查找OpenModelica可执行文件"""
        result = subprocess.run(['which', 'omc'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return None

    def _initialize_session(self) -> None:
        """初始化OpenModelica会话，包含重试机制"""
        if not self.is_available:
            return

        max_retries = 3
        retry_delay = 2  # 秒
        
        for attempt in range(max_retries):
            try:
                # 确保没有遗留的OMC进程
                self._cleanup_omc_processes()
                
                # 导入并初始化会话
                from OMPython import OMCSessionZMQ
                self.omc = OMCSessionZMQ(timeout=30)  # 增加超时时间
                
                # 验证会话
                version = self.omc.sendExpression('getVersion()')
                logger.info(f"OpenModelica连接成功，版本：{version}")
                return
                
            except Exception as e:
                logger.warning(f"OpenModelica会话初始化尝试 {attempt + 1}/{max_retries} 失败: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    continue
                
                logger.error(f"OpenModelica初始化失败，已达到最大重试次数: {e}")
                self.is_available = False
                self.status_message = f"OpenModelica初始化失败: {str(e)}"
                self.omc = None

    def _cleanup_omc_processes(self) -> None:
        """清理可能存在的OMC进程"""
        try:
            if sys.platform == 'darwin':  # macOS
                subprocess.run(['pkill', '-f', 'omc'], capture_output=True)
            elif sys.platform == 'linux':
                subprocess.run(['pkill', 'omc'], capture_output=True)
            elif sys.platform == 'win32':
                subprocess.run(['taskkill', '/F', '/IM', 'omc.exe'], capture_output=True)
        except Exception as e:
            logger.warning(f"清理OMC进程时出错: {e}")

    def simulate_model(self, modelica_code: str, model_name: str) -> Dict[str, Any]:
        """执行Modelica模型仿真"""
        if not self.is_available or not self.omc:
            return {
                'status': 'OpenModelica未安装，仿真功能不可用',
                'setup': None,
                'info': None
            }

        temp_file = None
        try:
            # 创建临时文件
            temp_file = self._create_temp_file(modelica_code)
            
            # 加载并编译模型
            if not self._load_model(temp_file):
                return {'status': '模型加载失败', 'setup': None, 'info': None}
            
            # 设置并执行仿真
            sim_setup = self._configure_simulation(model_name)
            sim_result = self._run_simulation(model_name)
            
            if not sim_result:
                return {'status': '仿真失败', 'setup': None, 'info': None}
            
            return {
                'status': '仿真成功',
                'setup': sim_setup,
                'info': sim_result
            }
            
        except Exception as e:
            logger.error(f"仿真过程出错: {e}")
            return {'status': f'仿真失败: {str(e)}', 'setup': None, 'info': None}
        finally:
            self._cleanup_temp_files(temp_file)

    def _create_temp_file(self, modelica_code: str) -> str:
        """创建临时Modelica文件"""
        with tempfile.NamedTemporaryFile(suffix='.mo', delete=False, mode='w', encoding='utf-8') as f:
            f.write(modelica_code)
            return f.name

    def _load_model(self, file_path: str) -> bool:
        """加载Modelica模型文件"""
        load_result = self.omc.sendExpression(f'loadFile("{file_path}")')
        if not load_result:
            logger.error(f"模型加载失败: {self.omc.sendExpression('getErrorString()')}")
            return False
        return True

    def _configure_simulation(self, model_name: str) -> Dict[str, Any]:
        """配置仿真参数"""
        sim_setup = {
            'startTime': 0.0,
            'stopTime': 10.0,
            'numberOfIntervals': 500,
            'tolerance': 1e-6,
            'method': 'dassl'
        }
        
        self.omc.sendExpression(f'setCommandLineOptions("-d=initialization,solver")')
        for key, value in sim_setup.items():
            self.omc.sendExpression(f'setSimulationOption("{key}", {value})')
            
        return sim_setup

    def _run_simulation(self, model_name: str) -> Optional[Dict[str, Any]]:
        """执行仿真"""
        sim_result = self.omc.sendExpression(f'simulate({model_name})')
        if not sim_result or 'timeTotal' not in sim_result:
            logger.error(f"仿真失败: {self.omc.sendExpression('getErrorString()')}")
            return None
        return sim_result

    def _cleanup_temp_files(self, temp_file: Optional[str]) -> None:
        """清理临时文件"""
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)

    def get_health_status(self) -> Dict[str, Any]:
        """获取OpenModelica的健康状态"""
        status = {
            'is_available': self.is_available,
            'status_message': self.status_message,
            'installation_path': os.environ.get('OPENMODELICAHOME', '未设置'),
            'version': None,
            'session_active': False,
            'details': {}
        }

        if self.is_available:
            try:
                # 检查版本
                version_result = subprocess.run(['omc', '--version'], capture_output=True, text=True)
                if version_result.returncode == 0:
                    status['version'] = version_result.stdout.strip()
                
                # 检查会话状态
                if self.omc:
                    try:
                        # 尝试执行一个简单的命令来验证会话
                        self.omc.sendExpression('getVersion()')
                        status['session_active'] = True
                        status['details']['session_type'] = 'OMCSessionZMQ'
                    except Exception as e:
                        status['details']['session_error'] = str(e)
                
                # 检查关键目录
                bin_path = os.path.join(os.environ.get('OPENMODELICAHOME', ''), 'bin')
                lib_path = os.path.join(os.environ.get('OPENMODELICAHOME', ''), 'lib')
                status['details']['directories'] = {
                    'bin': {
                        'exists': os.path.exists(bin_path),
                        'path': bin_path
                    },
                    'lib': {
                        'exists': os.path.exists(lib_path),
                        'path': lib_path
                    }
                }
                
            except Exception as e:
                logger.error(f"健康检查时出错: {e}")
                status['details']['check_error'] = str(e)
        
        return status

class ModelicaCodeGenerator:
    """Modelica代码生成器类"""
    
    def __init__(self):
        load_dotenv()
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2023-05-15",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

    def generate_code(self, prompt: str) -> Tuple[str, str]:
        """生成Modelica代码"""
        try:
            response = self._call_azure_openai(prompt)
            modelica_code = response.choices[0].message.content
            model_name = self._extract_model_name(modelica_code)
            return modelica_code, model_name
        except Exception as e:
            logger.error(f"代码生成失败: {e}")
            raise

    def _call_azure_openai(self, prompt: str) -> Any:
        """调用Azure OpenAI API"""
        return self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )

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
        model_match = re.search(r'model\s+(\w+)', modelica_code)
        if not model_match:
            raise ValueError('无法从生成的代码中识别模型名称')
        return model_match.group(1)

# 创建Flask应用
app = Flask(__name__, template_folder='../../templates')

# 初始化管理器
modelica_manager = OpenModelicaManager()
code_generator = ModelicaCodeGenerator()

@app.route('/')
def index():
    """渲染主页"""
    return render_template('index.html', openmodelica_available=modelica_manager.is_available)

@app.route('/api/generate', methods=['POST'])
def generate_modelica():
    """处理代码生成请求"""
    try:
        # 获取并验证输入
        data = request.json
        prompt = data.get('prompt')
        if not prompt:
            return jsonify({'error': '请提供模型描述'}), 400

        # 生成代码
        modelica_code, model_name = code_generator.generate_code(prompt)
        
        # 执行仿真
        simulation_result = modelica_manager.simulate_model(modelica_code, model_name)
        
        return jsonify({
            'modelica_code': modelica_code,
            'model_name': model_name,
            'simulation_result': simulation_result
        })
        
    except Exception as e:
        logger.error(f"处理请求时出错: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def check_health():
    """检查OpenModelica的健康状态"""
    try:
        health_status = modelica_manager.get_health_status()
        return jsonify(health_status)
    except Exception as e:
        logger.error(f"健康检查API出错: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5001) 