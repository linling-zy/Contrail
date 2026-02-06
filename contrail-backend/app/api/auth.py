"""
认证相关 API
提供登录、Token 刷新等功能
"""
from flask import request, jsonify
from app.api import api_bp
from app.extensions import db
from app.models import User
from app.utils.rsa_utils import get_rsa_utils
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity


@api_bp.route('/auth/public-key', methods=['GET'])
def get_public_key():
    """
    获取 RSA 公钥接口
    客户端使用此公钥加密密码后再发送
    返回: { "public_key": "..." }
    """
    rsa_utils = get_rsa_utils()
    return jsonify({
        'public_key': rsa_utils.get_public_key_pem()
    }), 200


@api_bp.route('/auth/login', methods=['POST'])
def login():
    """
    用户登录接口
    请求体: { "id_card_no": "身份证号", "password": "RSA加密后的密码(base64)" }
    注意：password 必须是使用 RSA 公钥加密后的 base64 字符串，请先调用 GET /api/auth/public-key 获取公钥
    返回: { "access_token": "...", "user": {...} }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    id_card_no = data.get('id_card_no')
    password = data.get('password')
    
    if not id_card_no or not password:
        return jsonify({'error': '身份证号和密码不能为空'}), 400
    
    # 强制要求密码必须使用 RSA 加密，解密密码
    try:
        rsa_utils = get_rsa_utils()
        password = rsa_utils.decrypt_password(password)
    except ValueError as e:
        return jsonify({'error': f'密码解密失败，请确保密码已使用RSA公钥加密: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'密码处理失败: {str(e)}'}), 400
    
    # 查找用户
    id_card_no = str(id_card_no).strip()
    user = User.query.filter_by(id_card_no=id_card_no).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': '身份证号或密码错误'}), 401
    
    # 生成 JWT Token
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200


@api_bp.route('/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    获取当前用户基本信息
    需要携带 JWT Token
    返回: { "user": {...} }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    return jsonify({
        'user': user.to_dict()
    }), 200

