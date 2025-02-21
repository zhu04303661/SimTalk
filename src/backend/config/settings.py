import os
from dotenv import load_dotenv
from pathlib import Path

# 加载.env文件
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    """应用配置类"""
    
    # Azure OpenAI 配置
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")

    
    
    OPENMODELICA_PATHS = [
        '/Applications/OpenModelica.app/Contents/Resources',
        '/opt/openmodelica',
    ]
    
    SIMULATION_SETTINGS = {
        'startTime': 0.0,
        'stopTime': 10.0,
        'numberOfIntervals': 500,
        'tolerance': 1e-6,
        'method': 'dassl'
    }

    @classmethod
    def validate_settings(cls):
        """验证配置是否完整"""
        required = [
            'AZURE_OPENAI_API_KEY',
            'AZURE_OPENAI_ENDPOINT',
            'AZURE_OPENAI_DEPLOYMENT_NAME',
            'AZURE_OPENAI_EMBEDDING_DEPLOYMENT'
        ]
        
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"缺少必要的配置项: {', '.join(missing)}") 