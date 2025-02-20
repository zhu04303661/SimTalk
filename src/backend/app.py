import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from flask import Flask, request, jsonify, render_template, Response, stream_with_context, send_from_directory
from dotenv import load_dotenv
import os
import tempfile
import subprocess
import json
import re
import time  # Add time module import
import logging
from typing import Dict, Tuple, Optional, Any
from openai import AzureOpenAI
from backend.modelica.manager import OpenModelicaManager
from backend.modelica.generator import ModelicaCodeGenerator
from backend.config.settings import Settings
from backend.utils.logger import setup_logger
from backend.prompts.modelica_prompts import  ModelicaPrompts
import ipdb
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
        """初始化OpenModelica会话"""
        if not self.is_available:
            return
            
        try:
            # 验证omc命令是否可用
            result = subprocess.run(['omc', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"OpenModelica连接成功，版本：{result.stdout.strip()}")
                self.omc = 'available'  # 标记为可用
                return
                
        except Exception as e:
            logger.error(f"OpenModelica初始化失败: {e}")
            self.is_available = False
            self.status_message = f"OpenModelica初始化失败: {str(e)}"
            self.omc = None

    def simulate_model(self, modelica_code: str, model_name: str) -> Dict[str, Any]:
        """执行Modelica模型仿真"""
        if not self.is_available:
            return {
                'status': 'OpenModelica未安装，仿真功能不可用',
                'setup': None,
                'info': None
            }

        try:
            # 创建基础temp目录
            base_temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
            os.makedirs(base_temp_dir, exist_ok=True)
            
            # 创建results目录
            results_dir = os.path.join(base_temp_dir, 'results')
            os.makedirs(results_dir, exist_ok=True)
            
            # 为当前任务创建唯一的目录名
            task_id = f"task_{model_name}_{int(time.time())}"
            task_dir = os.path.join(base_temp_dir, task_id)
            os.makedirs(task_dir, exist_ok=True)
            
            # 在任务目录中创建模型文件
            model_file = os.path.join(task_dir, f"{model_name}.mo")
            with open(model_file, 'w', encoding='utf-8') as f:
                f.write(modelica_code)
            
            # 读取仿真脚本模板
            template_path = os.path.join(os.path.dirname(__file__), 'simulation_template.mos')
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
            except FileNotFoundError:
                logger.error(f"找不到仿真脚本模板文件: {template_path}")
                return {
                    'status': '仿真失败',
                    'error': '找不到仿真脚本模板文件',
                    'info': None
                }
            
            # 在任务目录中创建仿真脚本
            sim_file = os.path.join(task_dir, f"{model_name}_sim.mos")
            with open(sim_file, 'w', encoding='utf-8') as f:
                # 使用转义的路径分隔符
                safe_task_dir = task_dir.replace('\\', '/')
                safe_model_file = model_file.replace('\\', '/')
                f.write(template_content.format(
                    temp_dir=safe_task_dir,
                    model_file=safe_model_file,
                    model_name=model_name
                ))

            # 执行仿真
            result = subprocess.run(
                ['omc', sim_file], 
                capture_output=True, 
                text=True,
                cwd=task_dir
            )
            
            logger.info(f"仿真脚本输出:\n{result.stdout}")
            if result.stderr:
                logger.error(f"仿真脚本错误:\n{result.stderr}")
            
            # 检查仿真结果文件
            result_file = os.path.join(task_dir, f"{model_name}_res.csv")  # Change temp_dir to task_dir
            
            if os.path.exists(result_file):
                # 将结果文件复制到持久化目录
                persistent_result_file = os.path.join(results_dir, f"{model_name}_res.csv")
                import shutil
                shutil.copy2(result_file, persistent_result_file)
                
                try:
                    import pandas as pd
                    
                    # 读取CSV结果文件
                    df = pd.read_csv(result_file)
                    
                    # 获取变量列表
                    variables = df.columns.tolist()
                    
                    # 解析仿真输出以获取详细信息
                    simulation_info = {
                        "raw_output": result.stdout,
                        "error_output": result.stderr
                    }
                    
                    # 从输出中提取关键信息
                    if "Simulation execution failed" in result.stdout:
                        status = "仿真失败"
                        error_msg = result.stdout
                    else:
                        status = "仿真成功"
                        error_msg = None
                        
                        # 尝试从输出中提取更多信息
                        time_stats = {}
                        for line in result.stdout.split('\n'):
                            if 'CPU time for integration' in line:
                                time_stats['integration_time'] = line.split(':')[1].strip()
                            elif 'CPU time for simulation' in line:
                                time_stats['total_time'] = line.split(':')[1].strip()
                        
                        if time_stats:
                            simulation_info["performance"] = time_stats
                    
                    simulation_result = {
                        "status": status,
                        "setup": {
                            "stopTime": 10.0,
                            "numberOfIntervals": 500,
                            "method": "dassl",
                            "tolerance": 1e-6
                        },
                        "info": simulation_info,
                        "error": error_msg,
                        "variables": variables,
                        "data": {
                            "time": df['time'].tolist(),
                            "values": {
                                col: df[col].tolist() 
                                for col in df.columns 
                                if col != 'time'
                            }
                        }
                    }
                    
                    # 如果有错误信息，添加到结果中
                    if result.stderr:
                        simulation_result["error_details"] = result.stderr
                    
                except Exception as e:
                    logger.error(f"处理结果文件失败: {e}")
                    simulation_result = {
                        "status": "仿真成功但处理结果失败",
                        "error": str(e),
                        "info": {
                            "raw_output": result.stdout,
                            "error_output": result.stderr
                        }
                    }
            else:
                # 解析仿真失败的原因
                error_analysis = self._analyze_simulation_error(result.stdout, result.stderr)
                error_info = (
                    f"仿真失败原因: {error_analysis}\n\n"
                    f"详细输出:\n{result.stdout}\n"
                    f"错误信息:\n{result.stderr}\n"
                    f"模型文件内容:\n{modelica_code}\n"
                )
                simulation_result = {
                    "status": "仿真失败",
                    "error": error_analysis,
                    "info": error_info
                }
            
            return simulation_result
            
        except Exception as e:
            logger.error(f"仿真过程出错: {e}")
            return {
                'status': f'仿真失败: {str(e)}',
                'setup': None,
                'info': None
            }
        finally:
            # Remove the cleanup code since we want to keep the task directory
            pass

    def _analyze_simulation_error(self, stdout: str, stderr: str) -> str:
        """分析仿真错误原因"""
        if not stdout and not stderr:
            return "未获取到仿真输出"
        
        error_patterns = [
            (r"Error: (.*?)(?=\n|$)", "编译错误"),
            (r"Failed to load model file: (.*?)(?=\n|$)", "模型加载失败"),
            (r"Simulation Failed\. (.*?)(?=\n|$)", "仿真执行失败"),
            (r"Error processing file: (.*?)(?=\n|$)", "文件处理错误")
        ]
        
        for pattern, error_type in error_patterns:
            if match := re.search(pattern, stdout + stderr):
                return f"{error_type}: {match.group(1)}"
            
        return "未知错误，请查看详细输出"

    def get_health_status(self) -> Dict[str, Any]:
        """获取OpenModelica的健康状态"""
        status = {
            'is_available': self.is_available,
            'status_message': self.status_message,
            'installation_path': os.environ.get('OPENMODELICAHOME', '未设置'),
            'version': None,
            'details': {}
        }

        if self.is_available:
            try:
                # 检查版本
                version_result = subprocess.run(['omc', '--version'], capture_output=True, text=True)
                if version_result.returncode == 0:
                    status['version'] = version_result.stdout.strip()
                
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
    
    def __init__(self, api_key: str, endpoint: str, deployment_name: str):
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version="2023-05-15",
            azure_endpoint=endpoint
        )
        self.modelica_prompts = ModelicaPrompts()

        self.deployment_name = deployment_name
       
        #self.system_prompt = self.modelica_prompts.get_system_prompt()
        #self.modelica_examples = self.modelica_prompts.get_modelica_examples()

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return self.system_prompt.format(example=self.modelica_examples)

    def generate_code(self, prompt: str) -> Tuple[str, str]:
        """生成Modelica代码"""
        try:
            # 首先检查是否有匹配的示例代码
            # 创建全局实例
            #example_code = self.modelica_prompts.find_matching_example(prompt)
            example_code = ''
            if example_code and example_code != (''):
                model_name = self._extract_model_name(example_code)
                return example_code, model_name
            else:
                # 使用GPT生成代码
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
app = Flask(__name__, 
            template_folder='../../templates',
            static_folder='../static')

# 初始化管理器
modelica_manager = OpenModelicaManager()
code_generator = ModelicaCodeGenerator(
    api_key=Settings.AZURE_OPENAI_API_KEY,
    endpoint=Settings.AZURE_OPENAI_ENDPOINT,
    deployment_name=Settings.AZURE_OPENAI_DEPLOYMENT_NAME
)

@app.route('/')
def index():
    """渲染主页"""
    return render_template('index.html', openmodelica_available=modelica_manager.is_available)

@app.route('/api/generate', methods=['POST'])
def generate_modelica():
    """处理代码生成请求"""
    try:
        data = request.json
        print("Received data:", data)  # 调试日志
        prompt = data.get('prompt')
        
        if not prompt:
            return jsonify({'error': '请提供模型描述'}), 400
        #ipdb.set_trace()
        def generate():
            try:
                yield "正在生成 Modelica 模型...\n"
                #ipdb.set_trace()

                # 生成代码
                modelica_code, model_name = code_generator.generate_code(prompt)
                
                # 发送生成的代码
                yield f"```modelica:{model_name}.mo\n"
                yield modelica_code
                yield "```\n"
                
                # 执行仿真
                # yield "正在执行仿真...\n"
                # simulation_result = modelica_manager.simulate_model(modelica_code, model_name)
                
                # # 发送仿真结果
                # yield f"simulation_result:{json.dumps(simulation_result, ensure_ascii=False)}\n"
                
                # if simulation_result['status'] == '仿真成功':
                #     yield "仿真已完成！\n"
                # else:
                #     yield f"仿真失败: {simulation_result['status']}\n"
                    
            except Exception as e:
                logger.error(f"代码生成失败: {e}")
                yield f"发生错误: {str(e)}\n"

        return Response(stream_with_context(generate()), mimetype='text/plain')
        
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

@app.route('/api/simulate', methods=['POST'])
def simulate_modelica():
    """处理仿真请求"""
    try:
        data = request.json
        modelica_code = data.get('modelica_code')
        model_name = data.get('model_name')
        
        if not modelica_code or not model_name:
            return jsonify({'error': '缺少必要参数'}), 400

        try:
            print("===========开始仿真===========")
            simulation_result = modelica_manager.simulate_model(modelica_code, model_name)
            print("===========仿真结束===========")
            return jsonify(simulation_result)
                
        except Exception as e:
            logger.error(f"仿真过程出错: {e}")
            return jsonify({'error': str(e)}), 500
        
    except Exception as e:
        logger.error(f"处理仿真请求时出错: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/results/<path:filename>')
def serve_result(filename):
    return send_from_directory('temp/results', filename)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5001)