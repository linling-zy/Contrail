"""
管理员学生管理 API
提供学生列表查询、状态更新等功能
需要管理员权限，普通管理员只能管理自己部门的学生
"""
from flask import request, jsonify
from app.api.admin_auth import admin_bp
from app.extensions import db
from app.models import User, AdminUser, Department, ScoreLog, Comment
from app.utils.permission import get_admin_accessible_query
from flask_jwt_extended import jwt_required, get_jwt_identity


# 状态枚举值
VALID_STAGES = ['preliminary', 'medical', 'political', 'admission']
VALID_STATUSES = ['qualified', 'unqualified', 'pending']


def check_admin_access_to_student(admin_id, student_id):
    """
    检查管理员是否有权限操作指定学生
    
    Args:
        admin_id: 管理员ID
        student_id: 学生ID
    
    Returns:
        tuple: (has_access: bool, student: User or None)
    """
    admin = AdminUser.query.get(admin_id)
    if not admin:
        return False, None
    
    student = User.query.get(student_id)
    if not student:
        return False, None
    
    # 超级管理员可以操作所有学生
    if admin.role == AdminUser.ROLE_SUPER:
        return True, student
    
    # 普通管理员只能操作自己部门的学生
    if not student.department_id:
        return False, student
    
    managed_departments = admin.managed_departments.all()
    managed_dept_ids = [dept.id for dept in managed_departments]
    
    if student.department_id in managed_dept_ids:
        return True, student
    
    return False, student


@admin_bp.route('/students', methods=['GET'])
@jwt_required()
def list_students():
    """
    获取学生列表（管理员权限）
    查询参数:
        - page: 页码（默认1）
        - per_page: 每页数量（默认20）
        - filter: 筛选类型（name/student_id/class_name）
        - keyword: 筛选关键词
    返回: { "total": n, "page": 1, "per_page": 20, "pages": n, "items": [...] }
    """
    admin_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    filter_type = request.args.get('filter')  # name/student_id/class_name
    keyword = request.args.get('keyword', '').strip()
    
    # 获取基础查询（已根据权限过滤）
    query = get_admin_accessible_query(User, admin_id)
    
    # 应用筛选条件
    if filter_type and keyword:
        if filter_type == 'name':
            # 按姓名筛选
            query = query.filter(User.name.like(f'%{keyword}%'))
        elif filter_type == 'student_id':
            # 按学号筛选
            query = query.filter(User.student_id.like(f'%{keyword}%'))
        elif filter_type == 'class_name':
            # 按班级名称筛选（需要通过部门关联）
            query = query.join(Department).filter(Department.class_name.like(f'%{keyword}%'))
        else:
            return jsonify({'error': f'无效的筛选类型: {filter_type}，支持的类型: name/student_id/class_name'}), 400
    
    # 分页查询
    pagination = query.order_by(User.id.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # 构建返回数据
    items = []
    for user in pagination.items:
        user_dict = user.to_dict(include_score=True)
        # 添加四阶段状态信息
        user_dict['process_status'] = {
            'preliminary': user.preliminary_status,
            'medical': user.medical_status,
            'political': user.political_status,
            'admission': user.admission_status,
        }
        items.append(user_dict)
    
    return jsonify({
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages,
        'items': items
    }), 200


@admin_bp.route('/students/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student_detail(student_id):
    """
    获取学生详情（管理员权限）
    返回: { "student": {...} }
    """
    admin_id = get_jwt_identity()
    
    # 检查权限
    has_access, student = check_admin_access_to_student(admin_id, student_id)
    
    if not student:
        return jsonify({'error': '学生不存在'}), 404
    
    if not has_access:
        return jsonify({'error': '无权访问该学生信息'}), 403
    
    student_dict = student.to_dict(include_score=True)
    # 添加四阶段状态信息
    student_dict['process_status'] = {
        'preliminary': student.preliminary_status,
        'medical': student.medical_status,
        'political': student.political_status,
        'admission': student.admission_status,
    }
    
    return jsonify({
        'student': student_dict
    }), 200


@admin_bp.route('/students/<int:student_id>/status', methods=['PUT'])
@jwt_required()
def update_student_status(student_id):
    """
    更新学生状态（管理员权限）
    请求体: {
        "stage": "preliminary" | "medical" | "political" | "admission",
        "status": "qualified" | "unqualified" | "pending"
    }
    返回: { "student": {...}, "message": "更新成功" }
    """
    admin_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    stage = data.get('stage')
    status = data.get('status')
    
    # 参数验证
    if not stage or not status:
        return jsonify({'error': 'stage 和 status 不能为空'}), 400
    
    if stage not in VALID_STAGES:
        return jsonify({
            'error': f'无效的阶段: {stage}，支持: {", ".join(VALID_STAGES)}'
        }), 400
    
    if status not in VALID_STATUSES:
        return jsonify({
            'error': f'无效的状态: {status}，支持: {", ".join(VALID_STATUSES)}'
        }), 400
    
    # 检查权限
    has_access, student = check_admin_access_to_student(admin_id, student_id)
    
    if not student:
        return jsonify({'error': '学生不存在'}), 404
    
    if not has_access:
        return jsonify({'error': '无权操作该学生'}), 403
    
    # 更新对应字段的状态
    if stage == 'preliminary':
        student.preliminary_status = status
    elif stage == 'medical':
        student.medical_status = status
    elif stage == 'political':
        student.political_status = status
    elif stage == 'admission':
        student.admission_status = status
    
    try:
        db.session.commit()
        
        # 重新查询以获取最新数据
        db.session.refresh(student)
        
        student_dict = student.to_dict(include_score=True)
        student_dict['process_status'] = {
            'preliminary': student.preliminary_status,
            'medical': student.medical_status,
            'political': student.political_status,
            'admission': student.admission_status,
        }
        
        return jsonify({
            'message': '状态更新成功',
            'student': student_dict
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新状态失败: {str(e)}'}), 500


@admin_bp.route('/score/adjust', methods=['POST'])
@jwt_required()
def adjust_score():
    """
    调整学生积分（管理员权限）
    请求体: {
        "user_id": 学生ID,
        "delta": 变动分数（正数为加分，负数为扣分）,
        "reason": "变动原因"
    }
    返回: { "score_log": {...}, "new_total_score": 85, "message": "积分调整成功" }
    """
    admin_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    user_id = data.get('user_id')
    delta = data.get('delta')
    reason = data.get('reason', '').strip()
    
    # 参数验证
    if user_id is None:
        return jsonify({'error': 'user_id 不能为空'}), 400
    
    if delta is None:
        return jsonify({'error': 'delta 不能为空'}), 400
    
    if not isinstance(delta, int):
        return jsonify({'error': 'delta 必须是整数'}), 400
    
    if delta == 0:
        return jsonify({'error': '变动分数不能为0'}), 400
    
    if not reason:
        return jsonify({'error': 'reason 不能为空'}), 400
    
    # 检查权限
    has_access, student = check_admin_access_to_student(admin_id, user_id)
    
    if not student:
        return jsonify({'error': '学生不存在'}), 404
    
    if not has_access:
        return jsonify({'error': '无权操作该学生'}), 403
    
    # 创建积分变动记录
    score_log = ScoreLog(
        user_id=user_id,
        delta=delta,
        reason=reason,
        type=ScoreLog.TYPE_MANUAL
    )
    
    try:
        db.session.add(score_log)
        db.session.commit()
        
        # 重新查询用户以获取最新总分（User 表的总分是动态计算的）
        db.session.refresh(student)
        
        return jsonify({
            'message': '积分调整成功',
            'score_log': score_log.to_dict(),
            'new_total_score': student.total_score
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'积分调整失败: {str(e)}'}), 500


@admin_bp.route('/students/<int:student_id>/comment', methods=['POST'])
@jwt_required()
def add_comment(student_id):
    """
    添加学生评语（管理员权限）
    请求体: {
        "content": "评语内容"
    }
    返回: { "comment": {...}, "message": "评语添加成功" }
    """
    admin_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    content = data.get('content', '').strip()
    
    # 参数验证
    if not content:
        return jsonify({'error': 'content 不能为空'}), 400
    
    # 检查权限
    has_access, student = check_admin_access_to_student(admin_id, student_id)
    
    if not student:
        return jsonify({'error': '学生不存在'}), 404
    
    if not has_access:
        return jsonify({'error': '无权操作该学生'}), 403
    
    # 获取管理员信息（用于记录评语作者）
    admin = AdminUser.query.get(admin_id)
    author_name = admin.name if admin else '系统'
    
    # 创建评语记录
    comment = Comment(
        user_id=student_id,
        content=content,
        author=author_name
    )
    
    try:
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({
            'message': '评语添加成功',
            'comment': comment.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'添加评语失败: {str(e)}'}), 500

