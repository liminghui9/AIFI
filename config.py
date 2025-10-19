import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # 文件上传配置
    UPLOAD_FOLDER = 'uploads'
    EXPORT_FOLDER = 'exports'
    DATA_FOLDER = 'data'
    STATIC_FOLDER = 'static'
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # OpenAI配置（兼容多种AI服务）
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_API_BASE = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')  # 智谱AI用glm-4，通义千问用qwen-turbo
    
    # 确保必要的目录存在
    @staticmethod
    def init_app():
        for folder in [Config.UPLOAD_FOLDER, Config.EXPORT_FOLDER, Config.DATA_FOLDER, 
                      os.path.join(Config.STATIC_FOLDER, 'charts')]:
            if not os.path.exists(folder):
                os.makedirs(folder)


