"""
证书相关 API
提供证书上传、查询、审核等功能
"""
import json
import logging
import mimetypes
import uuid
from datetime import datetime

from flask import request, jsonify
from app.api import api_bp
from app.extensions import db
from app.models import Certificate, User, CertificateType, Department
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.s3_presign import presign_get_object_url
from app.utils.minio_storage import upload_bytes

logger = logging.getLogger(__name__)

ALLOWED_EXTS = {"jpg", "png", "pdf"}
CONTENT_TYPES = {
    "jpg": "image/jpeg",
    "png": "image/png",
    "pdf": "application/pdf",
}


def _sniff_file_ext(data: bytes) -> str:
    """
    基于文件内容（magic bytes）判断真实类型，避免仅靠后缀名被伪造。
    仅支持 jpg/png/pdf，其他一律返回空串。
    """
    if not data:
        return ""

    # PDF: %PDF-
    if data.startswith(b"%PDF-"):
        return "pdf"

    # PNG: 89 50 4E 47 0D 0A 1A 0A
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"

    # JPEG: FF D8 FF
    if len(data) >= 3 and data[0:3] == b"\xff\xd8\xff":
        return "jpg"

    return ""


@api_bp.route('/certificate/upload', methods=['POST'])
@jwt_required()
def upload_certificate():
    """
    上传证书
    后端中转上传模式（multipart/form-data）：
    - file: 证书文件（jpg/png/pdf）
    - certName: 证书名称（或 name）
    - extraData: 额外数据（JSON字符串，可选）

    约定：
    - 绝不使用用户原始文件名作为存储名
    - 生成 object key：{year}/{month}/{uuid}.{ext}
    - 数据库仅保存 object key（落在 Certificate.image_url 字段中）
    """
    user_id = get_jwt_identity()

    file = request.files.get("file")
    cert_name = request.form.get("certName") or request.form.get("name")
    extra_data_str = request.form.get("extraData")

    if not cert_name:
        return jsonify({"code": 400, "msg": "certName is required"}), 400
    if not file:
        return jsonify({"code": 400, "msg": "file is required"}), 400

    # 校验扩展名（只使用扩展名判断类型；不使用原文件名作为存储名）
    filename = (file.filename or "").strip()
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTS:
        return jsonify({"code": 400, "msg": f"invalid file type, only {sorted(ALLOWED_EXTS)} allowed"}), 400

    data = file.read()
    if not data:
        return jsonify({"code": 400, "msg": "empty file"}), 400

    # 二次校验：基于内容识别真实类型，防止伪造后缀（比如 .jpg 实际是可执行/脚本/其他）
    sniffed_ext = _sniff_file_ext(data[:64])
    if sniffed_ext not in ALLOWED_EXTS:
        return jsonify({"code": 400, "msg": "invalid file content"}), 400
    if sniffed_ext != ext:
        return jsonify({"code": 400, "msg": "file extension does not match file content"}), 400

    now = datetime.utcnow()
    object_key = f"{now:%Y}/{now:%m}/{uuid.uuid4().hex}.{ext}"
    # Content-Type 以嗅探结果为准（不信任前端提供的 mimetype/文件名）
    content_type = CONTENT_TYPES.get(sniffed_ext) or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"code": 404, "msg": "user not found"}), 404

    # 解析 extraData（如果提供）
    extra_data = None
    if extra_data_str:
        try:
            extra_data = json.loads(extra_data_str)
        except json.JSONDecodeError:
            return jsonify({"code": 400, "msg": "extraData must be valid JSON"}), 400

    # 唯一性检查（硬编码逻辑）
    # 如果证书类型是"英语四级"、"英语六级"或"雅思IELTS"，检查是否已存在非驳回状态的同名证书
    single_upload_types = ["英语四级", "英语六级", "雅思IELTS"]
    if cert_name in single_upload_types:
        existing_cert = Certificate.query.filter_by(
            user_id=user_id,
            name=cert_name
        ).filter(
            Certificate.status != Certificate.STATUS_REJECTED
        ).first()
        
        if existing_cert:
            return jsonify({
                "code": 400,
                "msg": "该类型证书只允许上传一次，请勿重复提交"
            }), 400

    # 上传到 MinIO
    try:
        upload_bytes(object_key=object_key, data=data, content_type=content_type)
    except Exception:
        logger.exception("MinIO 上传失败: user_id=%s key=%s", user_id, object_key)
        return jsonify({"code": 500, "msg": "Upload failed"}), 500
    
    # 创建证书记录
    certificate = Certificate(
        user_id=user_id,
        name=cert_name,
        image_url=object_key,
        status=Certificate.STATUS_PENDING,
        extra_data=extra_data
    )
    
    try:
        db.session.add(certificate)
        db.session.commit()
        return jsonify({
            "code": 200,
            "msg": "Upload success",
            "data": {
                "fileId": certificate.id,
                "filePath": object_key,
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.exception("证书记录保存失败: user_id=%s key=%s", user_id, object_key)
        return jsonify({"code": 500, "msg": "Upload failed"}), 500


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

    cert_dicts = []
    any_presign_failed = False
    for cert in certificates:
        d = cert.to_dict()
        # 兼容前端字段命名：imgUrl 为临时授权访问链接；image_url 仍保留为 Object Key
        d["certName"] = cert.name
        d["imgUrl"] = presign_get_object_url(cert.image_url)
        if d["imgUrl"] is None and cert.image_url:
            any_presign_failed = True
        cert_dicts.append(d)

    return jsonify({
        'certificates': cert_dicts,
        **({'warning': '部分图片链接生成失败，请稍后重试'} if any_presign_failed else {})
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
    
    d = certificate.to_dict()
    d["certName"] = certificate.name
    d["imgUrl"] = presign_get_object_url(certificate.image_url)
    payload = {'certificate': d}
    if d["imgUrl"] is None and certificate.image_url:
        payload["warning"] = "图片链接生成失败，请稍后重试"
    return jsonify(payload), 200


@api_bp.route('/certificate/types', methods=['GET'])
@jwt_required()
def get_certificate_types():
    """
    获取当前用户部门需要提交的证书类型列表
    返回: {
      "certificate_types": [
        {
          "id": 1,
          "name": "英语四级",
          "description": "...",
          "is_required": true,
          "has_uploaded": false,  // 用户是否已上传该证书
          "upload_status": null   // 如果已上传，返回审核状态：0待审/1通过/2驳回
        }
      ]
    }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    if not user.department_id:
        return jsonify({
            'certificate_types': [],
            'message': '用户未绑定部门，无法获取证书类型列表'
        }), 200
    
    # 获取用户部门
    department = Department.query.get(user.department_id)
    if not department:
        return jsonify({'error': '部门不存在'}), 404
    
    # 获取该部门关联的所有证书类型
    certificate_types = department.certificate_types.order_by(CertificateType.id.asc()).all()
    
    # 获取用户已上传的所有证书（用于判断是否已上传）
    user_certificates = Certificate.query.filter_by(user_id=user_id).all()
    # 构建证书名称到证书对象的映射
    cert_name_map = {cert.name: cert for cert in user_certificates}
    
    result = []
    for cert_type in certificate_types:
        cert_dict = cert_type.to_dict()
        # 检查用户是否已上传该证书
        user_cert = cert_name_map.get(cert_type.name)
        if user_cert:
            cert_dict['has_uploaded'] = True
            cert_dict['upload_status'] = user_cert.status
            cert_dict['certificate_id'] = user_cert.id
        else:
            cert_dict['has_uploaded'] = False
            cert_dict['upload_status'] = None
            cert_dict['certificate_id'] = None
        result.append(cert_dict)
    
    return jsonify({
        'certificate_types': result
    }), 200


