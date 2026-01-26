"""
管理员证书审核 API
提供证书列表查询、审核等功能
需要管理员权限，普通管理员只能管理自己部门学生的证书
"""
from datetime import datetime
from flask import request, jsonify
from app.api.admin_auth import admin_bp
from app.extensions import db
from app.models import Certificate, User, AdminUser
from app.utils.permission import get_admin_accessible_query
from app.utils.s3_presign import presign_get_object_url
from flask_jwt_extended import jwt_required, get_jwt_identity


def check_admin_access_to_certificate(admin_id, certificate_id):
    """
    检查管理员是否有权限操作指定证书
    
    Args:
        admin_id: 管理员ID
        certificate_id: 证书ID
    
    Returns:
        tuple: (has_access: bool, certificate: Certificate or None)
    """
    admin = AdminUser.query.get(admin_id)
    if not admin:
        return False, None
    
    certificate = Certificate.query.get(certificate_id)
    if not certificate:
        return False, None
    
    # 获取证书所属的学生
    student = User.query.get(certificate.user_id)
    if not student:
        return False, certificate
    
    # 超级管理员可以操作所有证书
    if admin.role == AdminUser.ROLE_SUPER:
        return True, certificate
    
    # 普通管理员只能操作自己部门学生的证书
    if not student.department_id:
        return False, certificate
    
    managed_departments = admin.managed_departments.all()
    managed_dept_ids = [dept.id for dept in managed_departments]
    
    if student.department_id in managed_dept_ids:
        return True, certificate
    
    return False, certificate


@admin_bp.route('/certificates', methods=['GET'])
@jwt_required()
def list_certificates():
    """
    获取证书列表（管理员权限）
    查询参数:
        - status: 审核状态（0待审, 1通过, 2驳回）
        - page: 页码（默认1）
        - per_page: 每页数量（默认20）
    返回: { "total": n, "page": 1, "per_page": 20, "pages": n, "items": [...] }
    """
    admin_id = get_jwt_identity()
    status = request.args.get('status', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 获取基础查询（已根据权限过滤学生）
    # 需要通过 User 表 join Certificate 表进行权限过滤
    user_query = get_admin_accessible_query(User, admin_id)
    
    # 获取有权限访问的学生ID列表
    accessible_user_ids = [user.id for user in user_query.all()]
    
    if not accessible_user_ids:
        # 如果没有可访问的学生，返回空结果
        return jsonify({
            'total': 0,
            'page': page,
            'per_page': per_page,
            'pages': 0,
            'items': []
        }), 200
    
    # 构建证书查询，只查询有权限访问的学生的证书
    cert_query = Certificate.query.filter(Certificate.user_id.in_(accessible_user_ids))
    
    # 状态筛选
    if status is not None:
        if status not in [Certificate.STATUS_PENDING, Certificate.STATUS_APPROVED, Certificate.STATUS_REJECTED]:
            return jsonify({'error': f'无效的状态: {status}，支持: 0(待审)/1(通过)/2(驳回)'}), 400
        cert_query = cert_query.filter_by(status=status)
    
    # 分页查询
    pagination = cert_query.order_by(Certificate.upload_time.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # 构建返回数据
    items = []
    any_presign_failed = False
    for cert in pagination.items:
        # 获取学生信息
        student = User.query.get(cert.user_id)
        
        cert_dict = cert.to_dict()
        # 添加前端需要的字段
        cert_dict['certName'] = cert.name
        # 生成 Presigned URL
        cert_dict['imgUrl'] = presign_get_object_url(cert.image_url)
        if cert_dict['imgUrl'] is None and cert.image_url:
            any_presign_failed = True
        
        # 添加学生信息
        if student:
            cert_dict['student'] = {
                'id': student.id,
                'name': student.name,
                'student_id': student.student_id,
                'id_card_no': student.id_card_no,
                'department': student.department.to_dict() if student.department else None
            }
        else:
            cert_dict['student'] = None
        
        items.append(cert_dict)
    
    result = {
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages,
        'items': items
    }
    
    # 如果有 Presigned URL 生成失败的情况，添加警告
    if any_presign_failed:
        result['warning'] = '部分图片链接生成失败，请稍后重试'
    
    return jsonify(result), 200


@admin_bp.route('/certificates/<int:certificate_id>', methods=['GET'])
@jwt_required()
def get_certificate_detail(certificate_id):
    """
    获取证书详情（管理员权限）
    返回: { "certificate": {...} }
    """
    admin_id = get_jwt_identity()
    
    # 检查权限
    has_access, certificate = check_admin_access_to_certificate(admin_id, certificate_id)
    
    if not certificate:
        return jsonify({'error': '证书不存在'}), 404
    
    if not has_access:
        return jsonify({'error': '无权访问该证书'}), 403
    
    # 获取学生信息
    student = User.query.get(certificate.user_id)
    
    cert_dict = certificate.to_dict()
    cert_dict['certName'] = certificate.name
    cert_dict['imgUrl'] = presign_get_object_url(certificate.image_url)
    
    # 添加学生信息
    if student:
        cert_dict['student'] = {
            'id': student.id,
            'name': student.name,
            'student_id': student.student_id,
            'id_card_no': student.id_card_no,
            'department': student.department.to_dict() if student.department else None
        }
    else:
        cert_dict['student'] = None
    
    result = {'certificate': cert_dict}
    if cert_dict['imgUrl'] is None and certificate.image_url:
        result['warning'] = '图片链接生成失败，请稍后重试'
    
    return jsonify(result), 200


@admin_bp.route('/certificates/<int:certificate_id>/audit', methods=['POST'])
@jwt_required()
def audit_certificate(certificate_id):
    """
    审核证书（管理员权限）
    请求体: {
        "action": "approve" | "reject",
        "reject_reason": "驳回原因"  // 当 action=reject 时必填
    }
    返回: { "certificate": {...}, "message": "审核成功" }
    """
    admin_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    action = data.get('action')
    reject_reason = data.get('reject_reason', '').strip()
    
    # 参数验证
    if not action:
        return jsonify({'error': 'action 不能为空'}), 400
    
    if action not in ['approve', 'reject']:
        return jsonify({'error': f'无效的 action: {action}，支持: approve/reject'}), 400
    
    if action == 'reject' and not reject_reason:
        return jsonify({'error': '驳回时必须提供 reject_reason'}), 400
    
    # 检查权限
    has_access, certificate = check_admin_access_to_certificate(admin_id, certificate_id)
    
    if not certificate:
        return jsonify({'error': '证书不存在'}), 404
    
    if not has_access:
        return jsonify({'error': '无权审核该证书'}), 403
    
    # 更新审核状态
    if action == 'approve':
        certificate.status = Certificate.STATUS_APPROVED
        certificate.reject_reason = None
    elif action == 'reject':
        certificate.status = Certificate.STATUS_REJECTED
        certificate.reject_reason = reject_reason
    
    certificate.review_time = datetime.utcnow()
    
    try:
        db.session.commit()
        
        # 重新查询以获取最新数据
        db.session.refresh(certificate)
        
        # 获取学生信息
        student = User.query.get(certificate.user_id)
        
        cert_dict = certificate.to_dict()
        cert_dict['certName'] = certificate.name
        cert_dict['imgUrl'] = presign_get_object_url(certificate.image_url)
        
        # 添加学生信息
        if student:
            cert_dict['student'] = {
                'id': student.id,
                'name': student.name,
                'student_id': student.student_id,
                'id_card_no': student.id_card_no,
                'department': student.department.to_dict() if student.department else None
            }
        else:
            cert_dict['student'] = None
        
        return jsonify({
            'message': '审核成功',
            'certificate': cert_dict
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'审核失败: {str(e)}'}), 500

