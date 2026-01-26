"""
管理员认证相关 API
提供管理员登录、信息查询等功能
"""
from flask import request, jsonify
from flask import Blueprint
from app.extensions import db
from app.models import AdminUser
from app.utils.rsa_utils import get_rsa_utils
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

# 创建管理员 API 蓝图，前缀为 /api/admin
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/auth/public-key', methods=['GET'])
def get_public_key():
    """
    获取 RSA 公钥接口（管理员登录使用）
    返回: { "public_key": "..." }
    """
    rsa_utils = get_rsa_utils()
    return jsonify({
        'public_key': rsa_utils.get_public_key_pem()
    }), 200


@admin_bp.route('/auth/login', methods=['POST'])
def admin_login():
    """
    管理员登录接口
    请求体: { "username": "管理员账号", "password": "RSA加密后的密码(base64)" }
    注意：password 必须是使用 RSA 公钥加密后的 base64 字符串，请先调用 GET /api/admin/auth/public-key 获取公钥
    返回: { "access_token": "...", "admin": {...} }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    # 强制要求密码必须使用 RSA 加密，解密密码
    try:
        rsa_utils = get_rsa_utils()
        password = rsa_utils.decrypt_password(password)
    except ValueError as e:
        return jsonify({'error': f'密码解密失败，请确保密码已使用RSA公钥加密: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'密码处理失败: {str(e)}'}), 400
    
    # 查找管理员
    username = str(username).strip()
    admin = AdminUser.query.filter_by(username=username).first()
    
    if not admin or not admin.check_password(password):
        return jsonify({'error': '用户名或密码错误'}), 401
    
    # 生成 JWT Token
    # identity 存 admin_id，additional_claims 中存入 role
    access_token = create_access_token(
        identity=admin.id,
        additional_claims={'role': admin.role}
    )
    
    # 获取管理的部门ID列表
    managed_departments = admin.managed_departments.all()
    department_ids = [dept.id for dept in managed_departments]
    
    return jsonify({
        'access_token': access_token,
        'admin': {
            'id': admin.id,
            'username': admin.username,
            'name': admin.name,
            'role': admin.role,
            'department_ids': department_ids
        }
    }), 200


@admin_bp.route('/auth/info', methods=['GET'])
@jwt_required()
def get_admin_info():
    """
    获取当前管理员信息及其管理的部门ID列表
    需要携带 JWT Token
    返回: { "admin": {...}, "department_ids": [...] }
    """
    admin_id = get_jwt_identity()
    admin = AdminUser.query.get(admin_id)
    
    if not admin:
        return jsonify({'error': '管理员不存在'}), 404
    
    # 获取管理的部门ID列表
    managed_departments = admin.managed_departments.all()
    department_ids = [dept.id for dept in managed_departments]
    
    return jsonify({
        'admin': admin.to_dict(include_departments=False),
        'department_ids': department_ids
    }), 200

