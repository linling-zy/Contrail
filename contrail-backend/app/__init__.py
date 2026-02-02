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
    检查数据库是否已初始化，如果未初始化或版本不是最新的，则自动运行迁移到最新版本
    
    注意：
    - 对于 SQLite：数据库文件不存在时会自动创建
    - 对于 MySQL/PostgreSQL：需要确保数据库已存在（通常由 DBA 创建）
    """
    with app.app_context():
        try:
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
            
            # 尝试连接数据库并检查表是否存在
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            # 检查是否需要初始化或升级数据库
            needs_upgrade = False
            is_first_run = 'alembic_version' not in tables
            
            if is_first_run:
                logger.info("[数据库初始化] 检测到数据库未初始化，开始自动构建数据库...")
                needs_upgrade = True
            else:
                # 检查当前数据库版本是否是最新的
                try:
                    from alembic.script import ScriptDirectory
                    from alembic.runtime.migration import MigrationContext
                    
                    script = ScriptDirectory.from_config(alembic_cfg)
                    
                    # 处理多个heads的情况
                    try:
                        heads = script.get_heads()
                        if len(heads) > 1:
                            logger.warning(f"[数据库初始化] 检测到多个迁移分支: {heads}，将尝试升级到最新版本")
                            # 如果有多个heads，直接标记需要升级，让Alembic处理
                            needs_upgrade = True
                            head_revision = None
                        else:
                            head_revision = heads[0] if heads else None
                    except Exception as head_error:
                        # 如果get_heads()失败，尝试get_current_head()
                        try:
                            head_revision = script.get_current_head()
                        except Exception as e:
                            # 如果都失败，标记需要升级
                            logger.warning(f"[数据库初始化] 无法确定迁移版本，将尝试升级: {str(e)}")
                            needs_upgrade = True
                            head_revision = None
                    
                    if not needs_upgrade and head_revision:
                        with db.engine.connect() as connection:
                            context = MigrationContext.configure(connection)
                            current_revision = context.get_current_revision()
                        
                        if current_revision != head_revision:
                            logger.info(f"[数据库初始化] 检测到数据库版本不是最新的（当前: {current_revision}, 最新: {head_revision}），开始升级...")
                            needs_upgrade = True
                        else:
                            logger.debug(f"[数据库初始化] 数据库已是最新版本（{head_revision}），无需升级")
                except Exception as e:
                    logger.warning(f"[数据库初始化] 检查数据库版本时出错: {str(e)}，将尝试升级到最新版本")
                    needs_upgrade = True
            
            # 如果需要升级，运行迁移到最新版本
            if needs_upgrade:
                try:
                    # 尝试升级到head
                    command.upgrade(alembic_cfg, 'head')
                except Exception as upgrade_error:
                    # 如果升级失败且是因为多个heads，尝试升级到所有heads
                    if 'multiple heads' in str(upgrade_error).lower():
                        logger.warning(f"[数据库初始化] 检测到多个迁移分支，尝试升级所有分支...")
                        from alembic.script import ScriptDirectory
                        script = ScriptDirectory.from_config(alembic_cfg)
                        heads = script.get_heads()
                        # 升级到每个head（Alembic会处理依赖关系）
                        for head in heads:
                            try:
                                command.upgrade(alembic_cfg, head)
                                logger.info(f"[数据库初始化] 成功升级到分支: {head}")
                            except Exception as e:
                                logger.warning(f"[数据库初始化] 升级分支 {head} 时出错: {str(e)}")
                    else:
                        raise
                
                logger.info("[数据库初始化] 数据库迁移完成！")
                
                # 首次运行时，自动初始化证书类型数据
                if is_first_run:
                    logger.info("[数据库初始化] 首次运行，开始初始化证书类型数据...")
                    try:
                        from app.models import CertificateType
                        
                        CERTIFICATE_TYPES = [
                            {'name': '英语四级', 'description': '大学英语四级考试证书，单次上传，需要存储分数'},
                            {'name': '英语六级', 'description': '大学英语六级考试证书，单次上传，需要存储分数'},
                            {'name': '雅思IELTS', 'description': '国际英语语言测试系统证书，单次上传，需要存储听力、阅读、写作、口语、总分'},
                            {'name': '任职情况', 'description': '学生任职情况证明，可多次上传，需要存储任职时间、职务、集体获奖情况'},
                            {'name': '获奖情况', 'description': '学生获奖情况证明，可多次上传，需要存储奖励时间、主办单位、奖励级别、获奖等次'}
                        ]
                        
                        created_count = 0
                        for cert_type_data in CERTIFICATE_TYPES:
                            name = cert_type_data['name']
                            description = cert_type_data['description']
                            
                            existing = CertificateType.query.filter_by(name=name).first()
                            if not existing:
                                cert_type = CertificateType(
                                    name=name,
                                    description=description,
                                    is_required=True
                                )
                                db.session.add(cert_type)
                                created_count += 1
                        
                        if created_count > 0:
                            db.session.commit()
                            logger.info(f"[数据库初始化] 成功初始化 {created_count} 个证书类型")
                        else:
                            logger.info("[数据库初始化] 证书类型已存在，跳过初始化")
                    except Exception as e:
                        logger.warning(f"[数据库初始化] 初始化证书类型时出错: {str(e)}")
                        logger.warning("[数据库初始化] 可以稍后手动运行: python scripts/init_certificate_types.py")
                        db.session.rollback()
                
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
