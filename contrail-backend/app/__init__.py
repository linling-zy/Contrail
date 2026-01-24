"""
应用工厂模块 (Application Factory)
采用工厂模式创建 Flask 应用实例
初始化数据库、JWT、定时任务等扩展
"""
from flask import Flask
from config import config
from app.extensions import db, jwt, scheduler
from app.tasks import register_scheduled_tasks


def create_app(config_name='default'):
    """
    应用工厂函数
    根据配置名称创建并配置 Flask 应用实例
    
    Args:
        config_name: 配置名称 ('development', 'production', 'default')
    
    Returns:
        Flask 应用实例
    """
    app = Flask(__name__)
    
    # 加载配置
    config_class = config[config_name]
    
    # 如果是生产环境，验证必需的配置项
    if config_name == 'production':
        if not config_class.SECRET_KEY or not config_class.JWT_SECRET_KEY:
            raise ValueError("生产环境必须设置 SECRET_KEY 和 JWT_SECRET_KEY 环境变量")
    
    app.config.from_object(config_class)
    
    # 初始化扩展
    initialize_extensions(app)
    
    # 注册蓝图
    register_blueprints(app)
    
    # 注册定时任务
    register_scheduled_tasks()
    
    # 创建数据库表（开发环境使用）
    with app.app_context():
        db.create_all()
        print("[初始化] 数据库表已创建/更新")
    
    return app


def initialize_extensions(app):
    """
    初始化所有扩展插件
    """
    # 初始化数据库
    db.init_app(app)
    
    # 初始化 JWT
    jwt.init_app(app)
    
    # 初始化定时任务调度器
    scheduler.init_app(app)
    scheduler.start()
    print("[初始化] 定时任务调度器已启动")


def register_blueprints(app):
    """
    注册所有蓝图
    """
    from app.api import api_bp
    app.register_blueprint(api_bp)
    print("[初始化] API 蓝图已注册")
