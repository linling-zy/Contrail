"""
应用工厂模块 (Application Factory)
采用工厂模式创建 Flask 应用实例
初始化数据库、JWT、定时任务等扩展
"""
import logging
from flask import Flask
from config import config
from app.extensions import db, jwt, scheduler, migrate
from app.tasks import register_scheduled_tasks


logger = logging.getLogger(__name__)


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
    
    # 注意：不再使用 db.create_all()
    # 数据库迁移通过 Flask-Migrate 管理
    # 使用命令: flask db upgrade 来应用迁移
    
    return app


def initialize_extensions(app):
    """
    初始化所有扩展插件
    """
    # 初始化数据库
    db.init_app(app)
    
    # 初始化数据库迁移
    migrate.init_app(app, db)
    
    # 初始化 JWT
    jwt.init_app(app)
    
    # 初始化定时任务调度器
    scheduler.init_app(app)
    scheduler.start()
    logger.info("[初始化] 定时任务调度器已启动")


def register_blueprints(app):
    """
    注册所有蓝图
    """
    from app.api import api_bp
    from app.api.admin_auth import admin_bp
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    logger.info("[初始化] API 蓝图已注册")
    logger.info("[初始化] 管理员 API 蓝图已注册")
