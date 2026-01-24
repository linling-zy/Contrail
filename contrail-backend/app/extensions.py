"""
扩展模块
集中管理所有第三方插件的实例化
采用延迟初始化模式，避免循环导入
"""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_apscheduler import APScheduler

# 数据库 ORM 实例
db = SQLAlchemy()

# JWT 管理器实例
jwt = JWTManager()

# 定时任务调度器实例
scheduler = APScheduler()

