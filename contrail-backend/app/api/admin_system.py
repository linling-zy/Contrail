"""
超级管理员系统管理 API
提供管理员账号的创建、查询、修改等功能
提供证书类型管理和部门证书规则绑定功能
仅限超级管理员访问
"""
from flask import request, jsonify
from app.api.admin_auth import admin_bp
from app.extensions import db
from app.models import AdminUser, Department, CertificateType, Certificate, User
from app.utils.rsa_utils import get_rsa_utils
from app.utils.admin_permission import super_admin_required, admin_required
from app.utils.permission import get_admin_accessible_query
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime


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


# ==================== 证书类型管理 ====================

@admin_bp.route('/certificate-types', methods=['POST'])
@super_admin_required
def create_certificate_type():
    """
    创建证书类型（仅限超级管理员）
    请求体: {
        "name": "英语四级",
        "description": "大学英语四级考试证书",
        "is_required": true
    }
    返回: { "certificate_type": {...}, "message": "创建成功" }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    name = data.get('name', '').strip()
    description = data.get('description', '').strip() or None
    is_required = data.get('is_required', True)
    
    # 参数验证
    if not name:
        return jsonify({'error': '证书名称不能为空'}), 400
    
    # 检查名称是否已存在
    if CertificateType.query.filter_by(name=name).first():
        return jsonify({'error': '该证书类型名称已存在'}), 400
    
    # 创建证书类型
    cert_type = CertificateType(
        name=name,
        description=description,
        is_required=bool(is_required)
    )
    
    try:
        db.session.add(cert_type)
        db.session.commit()
        return jsonify({
            'message': '证书类型创建成功',
            'certificate_type': cert_type.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建证书类型失败: {str(e)}'}), 500


@admin_bp.route('/certificate-types', methods=['GET'])
@jwt_required()
def list_certificate_types():
    """
    获取所有证书类型列表（所有管理员都可以查看）
    返回: { "certificate_types": [...] }
    """
    certificate_types = CertificateType.query.order_by(CertificateType.id.asc()).all()
    
    return jsonify({
        'certificate_types': [cert_type.to_dict() for cert_type in certificate_types]
    }), 200


@admin_bp.route('/certificate-types/<int:cert_type_id>', methods=['DELETE'])
@super_admin_required
def delete_certificate_type(cert_type_id):
    """
    删除证书类型（仅限超级管理员）
    如果已有部门绑定或已有学生上传该证书，将返回错误
    返回: { "message": "删除成功" }
    """
    cert_type = CertificateType.query.get(cert_type_id)
    
    if not cert_type:
        return jsonify({'error': '证书类型不存在'}), 404
    
    # 检查是否有部门绑定了该证书类型
    departments_with_cert = cert_type.departments.all()
    if departments_with_cert:
        dept_names = [f"{dept.college}/{dept.grade}/{dept.major}/{dept.class_name}" for dept in departments_with_cert[:3]]
        dept_count = len(departments_with_cert)
        return jsonify({
            'error': f'无法删除：该证书类型已被 {dept_count} 个部门绑定',
            'departments': dept_names[:3]  # 只返回前3个作为示例
        }), 400
    
    # 检查是否有学生上传了该名称的证书
    certificates_count = Certificate.query.filter_by(name=cert_type.name).count()
    if certificates_count > 0:
        return jsonify({
            'error': f'无法删除：已有 {certificates_count} 个学生上传了该证书'
        }), 400
    
    try:
        db.session.delete(cert_type)
        db.session.commit()
        return jsonify({'message': '证书类型删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除证书类型失败: {str(e)}'}), 500


# ==================== 部门证书规则绑定 ====================

@admin_bp.route('/department/<int:dept_id>/bind-certs', methods=['POST'])
@super_admin_required
def bind_certificate_types_to_department(dept_id):
    """
    为部门绑定证书类型（仅限超级管理员）
    请求体: {
        "certificate_type_ids": [1, 2, 5]
    }
    返回: { "department": {...}, "certificate_types": [...], "message": "绑定成功" }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    certificate_type_ids = data.get('certificate_type_ids', [])
    
    # 参数验证
    if not isinstance(certificate_type_ids, list):
        return jsonify({'error': 'certificate_type_ids 必须是数组'}), 400
    
    # 获取部门
    department = Department.query.get(dept_id)
    if not department:
        return jsonify({'error': '部门不存在'}), 404
    
    # 验证证书类型ID是否存在
    if certificate_type_ids:
        valid_cert_types = CertificateType.query.filter(
            CertificateType.id.in_(certificate_type_ids)
        ).all()
        valid_ids = [ct.id for ct in valid_cert_types]
        invalid_ids = set(certificate_type_ids) - set(valid_ids)
        
        if invalid_ids:
            return jsonify({
                'error': f'以下证书类型ID不存在: {list(invalid_ids)}'
            }), 400
        
        # 更新部门与证书类型的关联（覆盖更新）
        department.certificate_types = valid_cert_types
    else:
        # 如果传入空数组，清空所有关联
        department.certificate_types = []
    
    try:
        db.session.commit()
        
        # 重新查询以获取最新数据
        db.session.refresh(department)
        bound_cert_types = department.certificate_types.all()
        
        return jsonify({
            'message': '证书类型绑定成功',
            'department': department.to_dict(),
            'certificate_types': [ct.to_dict() for ct in bound_cert_types]
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'绑定证书类型失败: {str(e)}'}), 500


# ==================== 部门管理 ====================

@admin_bp.route('/departments', methods=['POST'])
@super_admin_required
def create_department():
    """
    创建部门（仅限超级管理员）
    请求体: {
        "college": "计算机学院",
        "grade": "2023级",
        "major": "软件工程",
        "class_name": "2301班",
        "bonus_start_date": "2024-01-01"  // 可选，格式 YYYY-MM-DD
    }
    返回: { "department": {...}, "message": "创建成功" }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    college = data.get('college', '').strip() or None
    grade = data.get('grade', '').strip() or None
    major = data.get('major', '').strip() or None
    class_name = data.get('class_name', '').strip() or None
    bonus_start_date_str = data.get('bonus_start_date', '').strip() or None
    
    # 至少需要有一个字段不为空
    if not any([college, grade, major, class_name]):
        return jsonify({'error': '至少需要填写一个部门信息字段（学院/年级/专业/班级）'}), 400
    
    # 解析 bonus_start_date
    bonus_start_date = None
    if bonus_start_date_str:
        try:
            bonus_start_date = datetime.strptime(bonus_start_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'bonus_start_date 格式错误，应为 YYYY-MM-DD'}), 400
    
    # 创建部门
    department = Department(
        college=college,
        grade=grade,
        major=major,
        class_name=class_name,
        bonus_start_date=bonus_start_date
    )
    
    try:
        db.session.add(department)
        db.session.commit()
        return jsonify({
            'message': '部门创建成功',
            'department': department.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建部门失败: {str(e)}'}), 500


@admin_bp.route('/departments', methods=['GET'])
@jwt_required()
def list_departments():
    """
    获取部门列表（所有管理员都可以查看）
    查询参数: 
        - page: 页码（默认1）
        - per_page: 每页数量（默认20）
    返回: { "total": n, "page": 1, "per_page": 20, "pages": n, "items": [...] }
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 分页查询
    pagination = Department.query.order_by(Department.id.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return jsonify({
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages,
        'items': [dept.to_dict() for dept in pagination.items]
    }), 200


@admin_bp.route('/departments/<int:dept_id>', methods=['GET'])
@jwt_required()
def get_department(dept_id):
    """
    获取部门详情（所有管理员都可以查看）
    返回: { "department": {...} }
    """
    department = Department.query.get(dept_id)
    if not department:
        return jsonify({'error': '部门不存在'}), 404
    
    return jsonify({
        'department': department.to_dict()
    }), 200


@admin_bp.route('/departments/<int:dept_id>', methods=['PUT'])
@super_admin_required
def update_department(dept_id):
    """
    更新部门信息（仅限超级管理员）
    请求体: {
        "college": "计算机学院",  // 可选
        "grade": "2023级",  // 可选
        "major": "软件工程",  // 可选
        "class_name": "2301班",  // 可选
        "bonus_start_date": "2024-01-01"  // 可选，格式 YYYY-MM-DD，传 null 可清空
    }
    返回: { "department": {...}, "message": "更新成功" }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    department = Department.query.get(dept_id)
    if not department:
        return jsonify({'error': '部门不存在'}), 404
    
    # 更新字段（如果提供了）
    if 'college' in data:
        department.college = data.get('college', '').strip() or None
    if 'grade' in data:
        department.grade = data.get('grade', '').strip() or None
    if 'major' in data:
        department.major = data.get('major', '').strip() or None
    if 'class_name' in data:
        department.class_name = data.get('class_name', '').strip() or None
    
    # 更新 bonus_start_date
    if 'bonus_start_date' in data:
        bonus_start_date_str = data.get('bonus_start_date')
        if bonus_start_date_str is None:
            # 传 null 表示清空
            department.bonus_start_date = None
        elif isinstance(bonus_start_date_str, str) and bonus_start_date_str.strip():
            try:
                department.bonus_start_date = datetime.strptime(bonus_start_date_str.strip(), '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'bonus_start_date 格式错误，应为 YYYY-MM-DD'}), 400
        else:
            return jsonify({'error': 'bonus_start_date 格式错误'}), 400
    
    try:
        db.session.commit()
        return jsonify({
            'message': '部门信息更新成功',
            'department': department.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新部门失败: {str(e)}'}), 500


@admin_bp.route('/departments/<int:dept_id>', methods=['DELETE'])
@super_admin_required
def delete_department(dept_id):
    """
    删除部门（仅限超级管理员）
    如果部门下有学生，将返回错误
    返回: { "message": "删除成功" }
    """
    department = Department.query.get(dept_id)
    if not department:
        return jsonify({'error': '部门不存在'}), 404
    
    # 检查是否有学生绑定到该部门
    students_count = department.users.count()
    if students_count > 0:
        return jsonify({
            'error': f'无法删除：该部门下还有 {students_count} 个学生'
        }), 400
    
    try:
        db.session.delete(department)
        db.session.commit()
        return jsonify({'message': '部门删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除部门失败: {str(e)}'}), 500


@admin_bp.route('/dashboard/stats', methods=['GET'])
@admin_required
def get_dashboard_stats():
    """
    获取仪表盘统计数据（管理员权限）
    根据管理员权限返回对应的统计数据：
    - 超级管理员：返回所有学生和部门的统计
    - 普通管理员：只返回其管理的部门的学生统计
    
    返回: {
        "code": 200,
        "data": {
            "total_students": 100,
            "total_departments": 10,
            "process_stats": {
                "preliminary": {0: 10, 1: 80, 2: 10},
                "medical": {0: 20, 1: 70, 2: 10},
                "political": {0: 30, 1: 60, 2: 10},
                "admission": {0: 40, 1: 50, 2: 10}
            }
        },
        "message": "success"
    }
    注意：状态值转换为整数：pending(0), qualified(1), unqualified(2)
    """
    try:
        admin_id = get_jwt_identity()
        admin = AdminUser.query.get(admin_id)
        
        if not admin:
            return jsonify({
                'code': 404,
                'message': '管理员不存在'
            }), 404
        
        # 获取有权限访问的学生查询（已根据管理员权限过滤）
        students_query = get_admin_accessible_query(User, admin_id)
        
        # 统计总学生数（基于权限）
        total_students = students_query.count()
        
        # 统计总部门数（根据管理员权限）
        if admin.role == AdminUser.ROLE_SUPER:
            # 超级管理员可以看到所有部门
            total_departments = Department.query.count()
        else:
            # 普通管理员只能看到自己管理的部门
            total_departments = admin.managed_departments.count()
        
        # 统计四个阶段的状态分布（基于有权限的学生）
        # 状态值映射：'pending' -> 0, 'qualified' -> 1, 'unqualified' -> 2
        process_stats = {}
        
        # 四个阶段字段
        stages = {
            'preliminary': User.preliminary_status,
            'medical': User.medical_status,
            'political': User.political_status,
            'admission': User.admission_status
        }
        
        for stage_name, stage_field in stages.items():
            # 基于有权限的学生查询，统计各状态的人数
            pending_count = students_query.filter(stage_field == 'pending').count()
            qualified_count = students_query.filter(stage_field == 'qualified').count()
            unqualified_count = students_query.filter(stage_field == 'unqualified').count()
            
            process_stats[stage_name] = {
                0: pending_count,      # 进行中(0)
                1: qualified_count,    # 通过(1)
                2: unqualified_count   # 不通过(2)
            }
        
        return jsonify({
            'code': 200,
            'data': {
                'total_students': total_students,
                'total_departments': total_departments,
                'process_stats': process_stats
            },
            'message': 'success'
        }), 200
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取统计数据失败: {str(e)}'
        }), 500

