import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 基础配置
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # MySQL连接配置
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'appmanage')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '123456')
    encoded_password = quote_plus(password)
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

    # 连接池配置
    SQLALCHEMY_POOL_SIZE = 5          # 连接池大小
    SQLALCHEMY_MAX_OVERFLOW = 10      # 最大溢出连接数
    SQLALCHEMY_POOL_TIMEOUT = 30      # 获取连接超时时间(秒)
    SQLALCHEMY_POOL_RECYCLE = 3600    # 连接回收时间(秒)
    SQLALCHEMY_POOL_PRE_PING = True   # 连接前执行ping测试

    # 从环境变量读取敏感信息oss
    OSS_ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID')
    OSS_ACCESS_KEY_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET')
    OSS_REGION = os.getenv('OSS_REGION')
    OSS_BUCKET = os.getenv('OSS_BUCKET')
    OSS_ROLE_ARN = os.getenv('OSS_ROLE_ARN')  # RAM 角色 ARN
    OSS_TOKEN_EXPIRE = 900  # 临时凭证有效期（秒，建议 15 分钟）


    
class DevelopmentConfig(Config):
    DEBUG = True

    

class ProductionConfig(Config):
    pass