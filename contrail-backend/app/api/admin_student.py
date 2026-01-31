"""
管理员学生管理 API
提供学生列表查询、状态更新、批量注册等功能
需要管理员权限，普通管理员只能管理自己部门的学生
"""
import io
import os
import threading
import uuid
import zipfile
from datetime import datetime

from flask import request, jsonify, send_file, current_app, url_for, after_this_request
from app.api.admin_auth import admin_bp
from app.extensions import db
from app.models import User, AdminUser, Department, ScoreLog, Comment, Certificate
from app.utils.permission import get_admin_accessible_query
from app.utils.rsa_utils import get_rsa_utils
from flask_jwt_extended import jwt_required, get_jwt_identity
from docxtpl import DocxTemplate


# 状态枚举值
VALID_STAGES = ['preliminary', 'medical', 'political', 'admission']
VALID_STATUSES = ['qualified', 'unqualified', 'pending']

# 导出任务全局存储（仅进程内有效，适合作为简单方案）
EXPORT_TASKS = {}
EXPORT_TASKS_LOCK = threading.Lock()


def _extract_birth_and_gender(id_card_no: str):
    """
    从18位身份证号中提取出生年月和性别

    返回:
        birth_date: 'YYYY年MM月' 格式字符串
        gender: '男' 或 '女'
    """
    if not id_card_no or len(id_card_no) != 18:
        return '', ''

    try:
        birth_str = id_card_no[6:14]  # YYYYMMDD
        year = birth_str[0:4]
        month = birth_str[4:6]
        birth_date = f"{year}年{month}月"
    except Exception:
        birth_date = ''

    try:
        gender_code = int(id_card_no[16])
        gender = '男' if gender_code % 2 == 1 else '女'
    except Exception:
        gender = ''

    return birth_date, gender


def _run_department_export_task(app, task_id: str, admin_id: int, dept_id: int):
    """
    后台线程：部门学生档案批量导出

    步骤：
      1. 查询部门和学生
      2. 遍历学生，渲染 Word 模板
      3. 将所有文档打包为 ZIP 文件
      4. 更新 EXPORT_TASKS 中的任务状态
    """
    with app.app_context():
        try:
            # 再次检查管理员是否有权限访问该部门
            has_access, department = check_admin_access_to_department(admin_id, dept_id)
            if not department:
                with EXPORT_TASKS_LOCK:
                    task = EXPORT_TASKS.get(task_id)
                    if task is not None:
                        task.update({
                            'status': 'failed',
                            'error': '部门不存在',
                        })
                return

            if not has_access:
                with EXPORT_TASKS_LOCK:
                    task = EXPORT_TASKS.get(task_id)
                    if task is not None:
                        task.update({
                            'status': 'failed',
                            'error': '无权导出该部门学生档案',
                        })
                return

            # 查询部门下所有学生
            users = User.query.filter_by(department_id=dept_id).order_by(User.id.asc()).all()

            with EXPORT_TASKS_LOCK:
                task = EXPORT_TASKS.get(task_id)
                if task is None:
                    # 任务已被外部删除，直接结束
                    return
                task['total'] = len(users)
                task['progress'] = 0
                task['status'] = 'processing'

            # 模板路径
            template_path = os.path.join(app.root_path, 'templates', 'template_profile.docx')
            if not os.path.exists(template_path):
                with EXPORT_TASKS_LOCK:
                    task = EXPORT_TASKS.get(task_id)
                    if task is not None:
                        task.update({
                            'status': 'failed',
                            'error': f'模板文件不存在: {template_path}',
                        })
                return

            # 临时目录及 ZIP 路径
            temp_dir = os.path.join(app.instance_path, 'temp')
            os.makedirs(temp_dir, exist_ok=True)

            zip_filename_on_disk = f'export_{task_id}.zip'
            zip_path = os.path.join(temp_dir, zip_filename_on_disk)

            # 供下载展示的文件名（中文名）
            college = department.college or '未知学院'
            class_name = department.class_name or f'班级{department.id}'
            display_filename = f'{college}_{class_name}_学生档案.zip'

            # 创建 ZIP 文件并逐个学生写入文档
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for idx, user in enumerate(users):
                    birth_date, gender = _extract_birth_and_gender(user.id_card_no)

                    # 过滤掉系统加分的积分流水
                    score_logs_query = user.score_logs.filter(
                        ScoreLog.type != ScoreLog.TYPE_SYSTEM
                    ).order_by(ScoreLog.create_time.asc())
                    score_logs = []
                    for log in score_logs_query.all():
                        if log.delta is None:
                            continue
                        delta_str = f"+{log.delta}" if log.delta > 0 else str(log.delta)
                        score_logs.append({
                            'delta': delta_str,
                            'reason': log.reason or '',
                        })

                    # 仅保留审核通过的证书
                    certificates_query = user.certificates.filter_by(status=Certificate.STATUS_APPROVED)
                    certificates = [{'name': cert.name} for cert in certificates_query.all()]

                    dept = user.department or department
                    context = {
                        'name': user.name,
                        'id_card_no': user.id_card_no,
                        'student_id': user.student_id or '',
                        'college': dept.college or '',
                        'grade': dept.grade or '',
                        'total_score': user.total_score,
                        'birth_date': birth_date,
                        'gender': gender,
                        'score_logs': score_logs,
                        'certificates': certificates,
                    }

                    # 渲染模板
                    doc = DocxTemplate(template_path)
                    doc.render(context)
                    buffer = io.BytesIO()
                    doc.save(buffer)
                    buffer.seek(0)

                    # 为每个学生生成一个 docx 文件名
                    safe_name = (user.name or '未命名').replace('/', '_').replace('\\', '_')
                    stu_id_or_id = user.student_id or user.id_card_no
                    docx_filename = f'{safe_name}_{stu_id_or_id}.docx'

                    # 写入 ZIP
                    zipf.writestr(docx_filename, buffer.getvalue())

                    # 更新进度
                    with EXPORT_TASKS_LOCK:
                        task = EXPORT_TASKS.get(task_id)
                        if task is None:
                            # 任务被删除，提前终止
                            return
                        task['progress'] = idx + 1

            # 全部完成，更新任务状态
            with EXPORT_TASKS_LOCK:
                task = EXPORT_TASKS.get(task_id)
                if task is not None:
                    task.update({
                        'status': 'completed',
                        'file_path': zip_path,
                        'display_filename': display_filename,
                        'error': None,
                    })
        except Exception as e:
            # 异常处理：记录错误信息
            with EXPORT_TASKS_LOCK:
                task = EXPORT_TASKS.get(task_id)
                if task is not None:
                    task.update({
                        'status': 'failed',
                        'error': f'导出过程发生异常: {str(e)}',
                    })


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


def check_admin_access_to_department(admin_id, department_id):
    """
    检查管理员是否有权限在指定部门注册用户
    
    Args:
        admin_id: 管理员ID
        department_id: 部门ID
    
    Returns:
        tuple: (has_access: bool, department: Department or None)
    """
    admin = AdminUser.query.get(admin_id)
    if not admin:
        return False, None
    
    department = Department.query.get(department_id)
    if not department:
        return False, None
    
    # 超级管理员可以在所有部门注册用户
    if admin.role == AdminUser.ROLE_SUPER:
        return True, department
    
    # 普通管理员只能在自己管理的部门注册用户
    managed_departments = admin.managed_departments.all()
    managed_dept_ids = [dept.id for dept in managed_departments]
    
    if department_id in managed_dept_ids:
        return True, department
    
    return False, department


@admin_bp.route('/department/<int:dept_id>/export/start', methods=['POST'])
@jwt_required()
def start_department_export(dept_id):
    """
    发起部门学生档案批量导出任务（异步）
    返回: { "code": 200, "task_id": "..." }
    """
    admin_id = get_jwt_identity()

    # 基本权限校验，避免无效任务进入队列（线程中也会再次校验，双重保险）
    has_access, department = check_admin_access_to_department(admin_id, dept_id)
    if not department:
        return jsonify({'code': 404, 'error': '部门不存在'}), 404
    if not has_access:
        return jsonify({'code': 403, 'error': '无权导出该部门学生档案'}), 403

    task_id = uuid.uuid4().hex

    with EXPORT_TASKS_LOCK:
        EXPORT_TASKS[task_id] = {
            'status': 'processing',   # processing/completed/failed
            'progress': 0,
            'total': 0,
            'file_path': None,
            'display_filename': None,
            'error': None,
            'admin_id': admin_id,
            'dept_id': dept_id,
            'created_at': datetime.utcnow().isoformat(),
        }

    # 在线程中执行实际的导出逻辑
    app = current_app._get_current_object()
    thread = threading.Thread(
        target=_run_department_export_task,
        args=(app, task_id, admin_id, dept_id),
        daemon=True
    )
    thread.start()

    return jsonify({'code': 200, 'task_id': task_id}), 200


@admin_bp.route('/export/status/<task_id>', methods=['GET'])
@jwt_required()
def get_export_status(task_id):
    """
    查询导出任务进度
    返回: { "code": 200, "status": "...", "progress": 0, "total": 0, "download_url": null }
    """
    admin_id = get_jwt_identity()

    with EXPORT_TASKS_LOCK:
        task = EXPORT_TASKS.get(task_id)
        if not task:
            return jsonify({'code': 404, 'error': '任务不存在'}), 404

        # 只允许发起该任务的管理员查询（简单权限控制）
        if task.get('admin_id') != admin_id:
            return jsonify({'code': 403, 'error': '无权查询该导出任务'}), 403

        status = task.get('status', 'processing')
        progress = task.get('progress', 0)
        total = task.get('total', 0)
        error = task.get('error')

        download_url = None
        if status == 'completed':
            # 使用 url_for 生成下载链接（前端可直接使用）
            download_url = url_for('admin_bp.download_export_file', task_id=task_id)

    return jsonify({
        'code': 200,
        'task_id': task_id,
        'status': status,
        'progress': progress,
        'total': total,
        'error': error,
        'download_url': download_url,
    }), 200


@admin_bp.route('/export/download/<task_id>', methods=['GET'])
@jwt_required()
def download_export_file(task_id):
    """
    下载导出的 ZIP 文件
    仅当任务完成且文件存在时才允许下载
    """
    admin_id = get_jwt_identity()

    with EXPORT_TASKS_LOCK:
        task = EXPORT_TASKS.get(task_id)
        if not task:
            return jsonify({'code': 404, 'error': '任务不存在'}), 404

        # 简单权限控制：只能由发起任务的管理员下载
        if task.get('admin_id') != admin_id:
            return jsonify({'code': 403, 'error': '无权下载该导出文件'}), 403

        if task.get('status') != 'completed':
            return jsonify({'code': 400, 'error': '任务尚未完成，无法下载'}), 400

        file_path = task.get('file_path')
        display_filename = task.get('display_filename') or (os.path.basename(file_path) if file_path else None)

    if not file_path or not os.path.exists(file_path):
        return jsonify({'code': 410, 'error': '导出文件不存在或已被清理'}), 410

    # 下载完成后清理临时文件（可选）
    @after_this_request
    def _remove_file(response):
        try:
            os.remove(file_path)
        except OSError:
            pass
        return response

    return send_file(
        file_path,
        mimetype='application/zip',
        as_attachment=True,
        download_name=display_filename
    )


@admin_bp.route('/students/batch-register', methods=['POST'])
@jwt_required()
def batch_register():
    """
    批量注册学生（管理员权限）
    请求体: {
        "users": [
            {
                "id_card_no": "身份证号",
                "student_id": "学号(可选)",
                "name": "张三",
                "password": "RSA加密后的密码(base64)",
                "department_id": 1
            },
            ...
        ]
    }
    注意：password 必须是使用 RSA 公钥加密后的 base64 字符串，请先调用 GET /api/admin/auth/public-key 获取公钥
    返回: {
        "success_count": 2,
        "failed_count": 1,
        "success": [...],
        "failed": [...]
    }
    """
    admin_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    users_data = data.get('users', [])
    
    if not isinstance(users_data, list):
        return jsonify({'error': 'users 必须是数组'}), 400
    
    if not users_data:
        return jsonify({'error': 'users 数组不能为空'}), 400
    
    if len(users_data) > 100:
        return jsonify({'error': '单次最多只能注册100个用户'}), 400
    
    rsa_utils = get_rsa_utils()
    success_list = []
    failed_list = []
    
    for idx, user_data in enumerate(users_data):
        try:
            # 提取用户数据
            id_card_no = user_data.get('id_card_no')
            student_id = user_data.get('student_id')
            name = user_data.get('name')
            password = user_data.get('password')
            department_id = user_data.get('department_id')
            
            # 参数验证
            if not id_card_no or not name or not password:
                failed_list.append({
                    'index': idx,
                    'id_card_no': id_card_no or '',
                    'error': '身份证号、姓名和密码不能为空'
                })
                continue
            
            if not department_id:
                failed_list.append({
                    'index': idx,
                    'id_card_no': id_card_no,
                    'error': 'department_id 不能为空'
                })
                continue
            
            # 检查管理员是否有权限在该部门注册用户
            has_access, department = check_admin_access_to_department(admin_id, department_id)
            if not department:
                failed_list.append({
                    'index': idx,
                    'id_card_no': id_card_no,
                    'error': f'department_id {department_id} 不存在'
                })
                continue
            
            if not has_access:
                failed_list.append({
                    'index': idx,
                    'id_card_no': id_card_no,
                    'error': f'无权在部门 {department_id} 注册用户'
                })
                continue
            
            # 解密密码
            try:
                decrypted_password = rsa_utils.decrypt_password(password)
            except ValueError as e:
                failed_list.append({
                    'index': idx,
                    'id_card_no': id_card_no,
                    'error': f'密码解密失败，请确保密码已使用RSA公钥加密: {str(e)}'
                })
                continue
            except Exception as e:
                failed_list.append({
                    'index': idx,
                    'id_card_no': id_card_no,
                    'error': f'密码处理失败: {str(e)}'
                })
                continue
            
            # 身份证号格式校验
            id_card_no = str(id_card_no).strip()
            if len(id_card_no) != 18:
                failed_list.append({
                    'index': idx,
                    'id_card_no': id_card_no,
                    'error': '身份证号必须为18位'
                })
                continue
            
            if (not id_card_no[:17].isdigit()) or (not (id_card_no[17].isdigit() or id_card_no[17] in ('X', 'x'))):
                failed_list.append({
                    'index': idx,
                    'id_card_no': id_card_no,
                    'error': '身份证号格式不正确'
                })
                continue
            
            # 检查身份证号是否已存在
            if User.query.filter_by(id_card_no=id_card_no).first():
                failed_list.append({
                    'index': idx,
                    'id_card_no': id_card_no,
                    'error': '该身份证号已注册'
                })
                continue
            
            # 学号可选：如果提供，校验格式
            if student_id is not None and str(student_id).strip() != '':
                student_id = str(student_id).strip()
                if not student_id.isdigit():
                    failed_list.append({
                        'index': idx,
                        'id_card_no': id_card_no,
                        'error': '学号必须为纯数字'
                    })
                    continue
                if len(student_id) != 12:
                    failed_list.append({
                        'index': idx,
                        'id_card_no': id_card_no,
                        'error': '学号必须为12位数字'
                    })
                    continue
                # 学号唯一性检查
                if User.query.filter_by(student_id=student_id).first():
                    failed_list.append({
                        'index': idx,
                        'id_card_no': id_card_no,
                        'error': '该学号已注册'
                    })
                    continue
            else:
                student_id = None
            
            # 创建新用户
            user = User(
                id_card_no=id_card_no,
                student_id=student_id,
                name=name,
                department_id=department.id
            )
            user.set_password(decrypted_password)
            
            db.session.add(user)
            db.session.flush()  # 刷新以获取用户ID，但不提交事务
            
            success_list.append({
                'index': idx,
                'user': user.to_dict(include_score=False)
            })
            
        except Exception as e:
            failed_list.append({
                'index': idx,
                'id_card_no': user_data.get('id_card_no', ''),
                'error': f'处理失败: {str(e)}'
            })
    
    # 提交所有成功的用户
    try:
        db.session.commit()
        return jsonify({
            'success_count': len(success_list),
            'failed_count': len(failed_list),
            'success': success_list,
            'failed': failed_list
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': f'批量注册提交失败: {str(e)}',
            'success_count': 0,
            'failed_count': len(failed_list) + len(success_list),
            'success': [],
            'failed': failed_list + [{'index': item['index'], 'id_card_no': item['user']['id_card_no'], 'error': '数据库提交失败'} for item in success_list]
        }), 500

