"""
证书相关 API
提供证书上传、查询、审核等功能
"""
from flask import request, jsonify
from app.api import api_bp
from app.extensions import db
from app.models import Certificate, User
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import os


@api_bp.route('/certificate/upload', methods=['POST'])
@jwt_required()
def upload_certificate():
    """
    上传证书
    请求体: { "name": "英语四级证书", "image_url": "https://..." }
    注意: 实际项目中，image_url 应该通过文件上传接口获取
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    name = data.get('name')
    image_url = data.get('image_url')
    
    if not name or not image_url:
        return jsonify({'error': '证书名称和图片URL不能为空'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 创建证书记录
    certificate = Certificate(
        user_id=user_id,
        name=name,
        image_url=image_url,
        status=Certificate.STATUS_PENDING
    )
    
    try:
        db.session.add(certificate)
        db.session.commit()
        return jsonify({
            'message': '证书上传成功，等待审核',
            'certificate': certificate.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'证书上传失败: {str(e)}'}), 500


@api_bp.route('/certificate/list', methods=['GET'])
@jwt_required()
def get_certificates():
    """
    获取当前用户的证书列表
    查询参数: status (可选，筛选状态: 0待审/1通过/2驳回)
    """
    user_id = get_jwt_identity()
    status = request.args.get('status', type=int)
    
    query = Certificate.query.filter_by(user_id=user_id)
    
    if status is not None:
        query = query.filter_by(status=status)
    
    certificates = query.order_by(Certificate.upload_time.desc()).all()
    
    return jsonify({
        'certificates': [cert.to_dict() for cert in certificates]
    }), 200


@api_bp.route('/certificate/<int:cert_id>', methods=['GET'])
@jwt_required()
def get_certificate_detail(cert_id):
    """
    获取证书详情
    """
    user_id = get_jwt_identity()
    certificate = Certificate.query.filter_by(id=cert_id, user_id=user_id).first()
    
    if not certificate:
        return jsonify({'error': '证书不存在'}), 404
    
    return jsonify({
        'certificate': certificate.to_dict()
    }), 200


@api_bp.route('/certificate/<int:cert_id>/review', methods=['POST'])
@jwt_required()
def review_certificate(cert_id):
    """
    审核证书（需要管理员权限，这里简化处理）
    请求体: { "status": 1, "reject_reason": "..." }  (status: 1通过, 2驳回)
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    status = data.get('status')
    reject_reason = data.get('reject_reason', '')
    
    if status not in [Certificate.STATUS_APPROVED, Certificate.STATUS_REJECTED]:
        return jsonify({'error': '无效的审核状态'}), 400
    
    certificate = Certificate.query.get(cert_id)
    if not certificate:
        return jsonify({'error': '证书不存在'}), 404
    
    # 更新审核状态
    certificate.status = status
    certificate.review_time = datetime.utcnow()
    
    if status == Certificate.STATUS_REJECTED:
        certificate.reject_reason = reject_reason or '审核未通过'
    
    try:
        db.session.commit()
        return jsonify({
            'message': '审核完成',
            'certificate': certificate.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'审核失败: {str(e)}'}), 500

