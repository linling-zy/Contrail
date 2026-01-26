"""
超级管理员系统管理 API
提供管理员账号的创建、查询、修改等功能
仅限超级管理员访问
"""
from flask import request, jsonify
from app.api.admin_auth import admin_bp
from app.extensions import db
from app.models import AdminUser, Department
from app.utils.rsa_utils import get_rsa_utils
from app.utils.admin_permission import super_admin_required
from flask_jwt_extended import jwt_required, get_jwt_identity


@admin_bp.route('/admins', methods=['POST'])
@super_admin_required
def create_admin():
    """
    创建管理员账号（仅限超级管理员）
    请求体: {
        "username": "管理员账号",
        "password": "RSA加密后的密码(base64)",
        "name": "真实姓名",
        "role": "super" | "normal",
        "department_ids": [1, 2, 3]  // 可选，普通管理员需要指定管理的部门
    }
    返回: { "admin": {...}, "message": "创建成功" }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')
    role = data.get('role', AdminUser.ROLE_NORMAL)
    department_ids = data.get('department_ids', [])
    
    # 参数验证
    if not username or not password or not name:
        return jsonify({'error': '用户名、密码和姓名不能为空'}), 400
    
    # 角色验证
    if role not in [AdminUser.ROLE_SUPER, AdminUser.ROLE_NORMAL]:
        return jsonify({'error': '无效的角色，必须是 super 或 normal'}), 400
    
    # 普通管理员必须指定至少一个部门
    if role == AdminUser.ROLE_NORMAL and not department_ids:
        return jsonify({'error': '普通管理员必须指定至少一个管理的部门'}), 400
    
    # 检查用户名是否已存在
    if AdminUser.query.filter_by(username=username).first():
        return jsonify({'error': '该用户名已存在'}), 400
    
    # 解密密码
    try:
        rsa_utils = get_rsa_utils()
        password = rsa_utils.decrypt_password(password)
    except ValueError as e:
        return jsonify({'error': f'密码解密失败，请确保密码已使用RSA公钥加密: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'密码处理失败: {str(e)}'}), 400
    
    # 验证部门ID是否存在
    if department_ids:
        valid_departments = Department.query.filter(Department.id.in_(department_ids)).all()
        valid_dept_ids = [dept.id for dept in valid_departments]
        invalid_ids = set(department_ids) - set(valid_dept_ids)
        if invalid_ids:
            return jsonify({'error': f'以下部门ID不存在: {list(invalid_ids)}'}), 400
    
    # 创建管理员
    admin = AdminUser(
        username=username.strip(),
        name=name.strip(),
        role=role
    )
    admin.set_password(password)
    
    try:
        db.session.add(admin)
        db.session.flush()  # 获取 admin.id
        
        # 绑定部门（如果是普通管理员）
        if role == AdminUser.ROLE_NORMAL and department_ids:
            departments = Department.query.filter(Department.id.in_(department_ids)).all()
            admin.managed_departments.extend(departments)
        
        db.session.commit()
        
        # 获取管理的部门ID列表
        managed_departments = admin.managed_departments.all()
        department_ids_result = [dept.id for dept in managed_departments]
        
        return jsonify({
            'message': '管理员创建成功',
            'admin': {
                'id': admin.id,
                'username': admin.username,
                'name': admin.name,
                'role': admin.role,
                'department_ids': department_ids_result,
                'create_time': admin.create_time.isoformat() if admin.create_time else None
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建管理员失败: {str(e)}'}), 500


@admin_bp.route('/admins', methods=['GET'])
@super_admin_required
def list_admins():
    """
    获取管理员列表（仅限超级管理员）
    查询参数: 
        - page: 页码（默认1）
        - per_page: 每页数量（默认20）
        - role: 筛选角色（可选，super 或 normal）
    返回: { "total": n, "page": 1, "per_page": 20, "pages": n, "items": [...] }
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    role_filter = request.args.get('role')
    
    # 构建查询
    query = AdminUser.query
    
    # 角色筛选
    if role_filter in [AdminUser.ROLE_SUPER, AdminUser.ROLE_NORMAL]:
        query = query.filter_by(role=role_filter)
    
    # 分页查询
    pagination = query.order_by(AdminUser.id.desc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # 构建返回数据
    items = []
    for admin in pagination.items:
        managed_departments = admin.managed_departments.all()
        department_ids = [dept.id for dept in managed_departments]
        
        admin_dict = admin.to_dict(include_departments=False)
        admin_dict['department_ids'] = department_ids
        items.append(admin_dict)
    
    return jsonify({
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages,
        'items': items
    }), 200


@admin_bp.route('/admins/<int:admin_id>', methods=['PUT'])
@super_admin_required
def update_admin(admin_id):
    """
    修改管理员信息（仅限超级管理员）
    请求体: {
        "name": "新姓名",  // 可选
        "password": "RSA加密后的新密码(base64)",  // 可选
        "role": "super" | "normal",  // 可选
        "department_ids": [1, 2, 3]  // 可选，修改管理的部门
    }
    返回: { "admin": {...}, "message": "更新成功" }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    admin = AdminUser.query.get(admin_id)
    if not admin:
        return jsonify({'error': '管理员不存在'}), 404
    
    # 不能修改自己的角色（防止超级管理员误操作）
    current_admin_id = get_jwt_identity()
    if admin_id == current_admin_id and 'role' in data:
        return jsonify({'error': '不能修改自己的角色'}), 400
    
    # 更新姓名
    if 'name' in data:
        name = str(data.get('name')).strip()
        if name:
            admin.name = name
    
    # 更新密码
    if 'password' in data:
        password = data.get('password')
        try:
            rsa_utils = get_rsa_utils()
            password = rsa_utils.decrypt_password(password)
            admin.set_password(password)
        except ValueError as e:
            return jsonify({'error': f'密码解密失败，请确保密码已使用RSA公钥加密: {str(e)}'}), 400
        except Exception as e:
            return jsonify({'error': f'密码处理失败: {str(e)}'}), 400
    
    # 更新角色
    if 'role' in data:
        role = data.get('role')
        if role not in [AdminUser.ROLE_SUPER, AdminUser.ROLE_NORMAL]:
            return jsonify({'error': '无效的角色，必须是 super 或 normal'}), 400
        admin.role = role
    
    # 更新管理的部门
    if 'department_ids' in data:
        department_ids = data.get('department_ids', [])
        
        # 如果角色是普通管理员，必须指定至少一个部门
        final_role = admin.role if 'role' not in data else data.get('role')
        if final_role == AdminUser.ROLE_NORMAL and not department_ids:
            return jsonify({'error': '普通管理员必须指定至少一个管理的部门'}), 400
        
        # 验证部门ID是否存在
        if department_ids:
            valid_departments = Department.query.filter(Department.id.in_(department_ids)).all()
            valid_dept_ids = [dept.id for dept in valid_departments]
            invalid_ids = set(department_ids) - set(valid_dept_ids)
            if invalid_ids:
                return jsonify({'error': f'以下部门ID不存在: {list(invalid_ids)}'}), 400
        
        # 更新部门关联
        if department_ids:
            departments = Department.query.filter(Department.id.in_(department_ids)).all()
            admin.managed_departments = departments
        else:
            # 如果是超级管理员，清空部门关联
            admin.managed_departments = []
    
    try:
        db.session.commit()
        
        # 获取管理的部门ID列表
        managed_departments = admin.managed_departments.all()
        department_ids_result = [dept.id for dept in managed_departments]
        
        return jsonify({
            'message': '管理员信息更新成功',
            'admin': {
                'id': admin.id,
                'username': admin.username,
                'name': admin.name,
                'role': admin.role,
                'department_ids': department_ids_result,
                'create_time': admin.create_time.isoformat() if admin.create_time else None
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新管理员失败: {str(e)}'}), 500


@admin_bp.route('/admins/<int:admin_id>', methods=['GET'])
@super_admin_required
def get_admin_detail(admin_id):
    """
    获取管理员详情（仅限超级管理员）
    返回: { "admin": {...} }
    """
    admin = AdminUser.query.get(admin_id)
    if not admin:
        return jsonify({'error': '管理员不存在'}), 404
    
    # 获取管理的部门ID列表
    managed_departments = admin.managed_departments.all()
    department_ids = [dept.id for dept in managed_departments]
    
    admin_dict = admin.to_dict(include_departments=True)
    admin_dict['department_ids'] = department_ids
    
    return jsonify({
        'admin': admin_dict
    }), 200


@admin_bp.route('/admins/<int:admin_id>', methods=['DELETE'])
@super_admin_required
def delete_admin(admin_id):
    """
    删除管理员（仅限超级管理员）
    不能删除自己
    返回: { "message": "删除成功" }
    """
    admin = AdminUser.query.get(admin_id)
    if not admin:
        return jsonify({'error': '管理员不存在'}), 404
    
    # 不能删除自己
    current_admin_id = get_jwt_identity()
    if admin_id == current_admin_id:
        return jsonify({'error': '不能删除自己的账号'}), 400
    
    try:
        db.session.delete(admin)
        db.session.commit()
        return jsonify({'message': '管理员删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除管理员失败: {str(e)}'}), 500

