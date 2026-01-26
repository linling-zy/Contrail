"""
API 蓝图模块
统一注册所有 API 路由
"""
from flask import Blueprint

# 创建 API 蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

# 导入各个路由模块（在蓝图注册后导入，避免循环导入）
from app.api import auth, student, certificate, admin_auth, admin_system, admin_student, admin_cert

