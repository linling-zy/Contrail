"""
管理员权限检查工具
提供权限验证装饰器和辅助函数
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import AdminUser


def super_admin_required(f):
    """
    装饰器：要求当前用户必须是超级管理员
    使用方式：
        @admin_bp.route('/some-route')
        @super_admin_required
        def some_function():
            ...
    """
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        admin_id = get_jwt_identity()
        claims = get_jwt()
        
        # 从 claims 中获取 role，如果没有则从数据库查询
        role = claims.get('role')
        if not role:
            admin = AdminUser.query.get(admin_id)
            if not admin:
                return jsonify({'error': '管理员不存在'}), 404
            role = admin.role
        
        # 检查是否是超级管理员
        if role != AdminUser.ROLE_SUPER:
            return jsonify({'error': '权限不足，需要超级管理员权限'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


def get_current_admin():
    """
    获取当前登录的管理员对象
    需要在 @jwt_required() 装饰的函数中使用
    
    Returns:
        AdminUser: 管理员对象，如果不存在则返回 None
    """
    admin_id = get_jwt_identity()
    return AdminUser.query.get(admin_id)


def is_super_admin(admin_id=None):
    """
    检查指定管理员是否是超级管理员
    如果不提供 admin_id，则从当前 JWT 中获取
    
    Args:
        admin_id: 管理员ID（可选）
    
    Returns:
        bool: 是否是超级管理员
    """
    if admin_id is None:
        admin_id = get_jwt_identity()
    
    admin = AdminUser.query.get(admin_id)
    if not admin:
        return False
    
    return admin.role == AdminUser.ROLE_SUPER

