"""
配置文件
支持开发环境 (Development) 和生产环境 (Production)
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# 在导入配置类之前先加载 .env 文件
load_dotenv()


class Config:
    """基础配置类"""
    # 应用密钥 (生产环境应从环境变量读取)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # JWT 配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)  # Token 24小时过期
    JWT_ALGORITHM = 'HS256'
    
    # 定时任务配置
    SCHEDULER_API_ENABLED = True  # 启用调度器 API (用于查看任务状态)
    SCHEDULER_TIMEZONE = 'Asia/Shanghai'  # 时区设置为中国时区
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 最大上传文件大小 16MB
    UPLOAD_FOLDER = 'uploads'  # 证书图片上传目录
    
    # 基础分默认值
    DEFAULT_BASE_SCORE = 80


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    # SQLite 数据库 (开发环境)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///contrail_dev.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True  # 打印 SQL 语句 (便于调试)


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    # MySQL 数据库 (生产环境)
    # 格式: mysql+pymysql://username:password@host:port/database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://user:password@localhost:3306/contrail_prod'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # 生产环境必须从环境变量读取密钥
    # 注意：验证将在应用工厂中进行，而不是在类定义时
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')


# 配置字典，方便根据环境变量选择配置
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

