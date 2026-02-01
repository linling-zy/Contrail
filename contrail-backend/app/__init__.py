"""
应用工厂模块 (Application Factory)
采用工厂模式创建 Flask 应用实例
初始化数据库、JWT、定时任务等扩展
"""
import logging
import os
from flask import Flask
from flask_cors import CORS
from sqlalchemy import inspect
from alembic import command
from alembic.config import Config
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
    
    # 配置 CORS，允许来自前端的跨域请求
    CORS(app, 
         origins=['http://localhost:5173'],
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # 初始化扩展
    initialize_extensions(app)
    
    # 自动构建数据库（首次启动时）
    auto_setup_database(app)
    
    # 注册蓝图
    register_blueprints(app)
    
    # 注册定时任务
    register_scheduled_tasks()
    
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


def auto_setup_database(app):
    """
    自动构建数据库（首次启动时）
    检查数据库是否已初始化，如果未初始化则自动运行迁移
    
    注意：
    - 对于 SQLite：数据库文件不存在时会自动创建
    - 对于 MySQL/PostgreSQL：需要确保数据库已存在（通常由 DBA 创建）
    """
    with app.app_context():
        try:
            # 尝试连接数据库并检查表是否存在
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'alembic_version' not in tables:
                logger.info("[数据库初始化] 检测到数据库未初始化，开始自动构建数据库...")
                
                # 获取项目根目录（app/__init__.py 的父目录的父目录）
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                migrations_dir = os.path.join(project_root, 'migrations')
                alembic_ini_path = os.path.join(migrations_dir, 'alembic.ini')
                
                if not os.path.exists(alembic_ini_path):
                    logger.warning(f"[数据库初始化] 未找到 Alembic 配置文件: {alembic_ini_path}")
                    logger.warning("[数据库初始化] 请手动运行: flask db upgrade")
                    return
                
                # 读取并配置 Alembic
                alembic_cfg = Config(alembic_ini_path)
                
                # 设置 script_location（指向 migrations 目录）
                alembic_cfg.set_main_option('script_location', migrations_dir)
                
                # 设置数据库 URL（使用 Flask 应用的数据库配置）
                alembic_cfg.set_main_option('sqlalchemy.url', str(db.engine.url))
                
                # 运行迁移到最新版本
                command.upgrade(alembic_cfg, 'head')
                
                logger.info("[数据库初始化] 数据库构建完成！")
            else:
                logger.debug("[数据库初始化] 数据库已存在，跳过自动构建")
                
        except Exception as e:
            # 如果是数据库连接错误，可能是数据库不存在（MySQL/PostgreSQL）
            error_msg = str(e).lower()
            if 'does not exist' in error_msg or 'unknown database' in error_msg or ('database' in error_msg and 'not found' in error_msg):
                logger.error(f"[数据库初始化] 数据库不存在或无法连接: {str(e)}")
                logger.warning("[数据库初始化] 请先创建数据库，然后重新启动服务")
            else:
                logger.error(f"[数据库初始化] 自动构建数据库时发生错误: {str(e)}")
                logger.warning("[数据库初始化] 如果这是首次启动，请手动运行: flask db upgrade")
            # 不抛出异常，允许应用继续启动（用户可能想手动处理）


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
