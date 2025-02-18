import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """应用配置类"""
    
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
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