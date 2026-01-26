"""
权限控制辅助模块
提供管理员权限查询和数据过滤功能
"""
from app.extensions import db
from app.models import AdminUser


def get_admin_accessible_query(model, admin_id):
    """
    根据管理员权限返回可访问的数据查询对象
    
    逻辑：
    - 如果是 super 管理员，返回 model.query (无限制)
    - 如果是 normal 管理员，返回 model.query.filter(model.department_id.in_(dept_ids))
    
    Args:
        model: SQLAlchemy 模型类（需要有 department_id 字段）
        admin_id: 管理员ID
    
    Returns:
        SQLAlchemy Query 对象，已根据权限过滤
    """
    admin = AdminUser.query.get(admin_id)
    
    if not admin:
        # 如果管理员不存在，返回空查询
        return model.query.filter(False)
    
    # 超级管理员可以访问所有数据
    if admin.role == AdminUser.ROLE_SUPER:
        return model.query
    
    # 普通管理员只能访问其管理的部门的数据
    # 获取管理员管理的部门ID列表
    managed_departments = admin.managed_departments.all()
    dept_ids = [dept.id for dept in managed_departments]
    
    if not dept_ids:
        # 如果没有管理的部门，返回空查询
        return model.query.filter(False)
    
    # 返回过滤后的查询
    return model.query.filter(model.department_id.in_(dept_ids))

