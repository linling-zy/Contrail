"""
认证相关 API
提供登录、注册、Token 刷新等功能
"""
from flask import request, jsonify
from app.api import api_bp
from app.extensions import db
from app.models import User, Department
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


@api_bp.route('/auth/register', methods=['POST'])
def register():
    """
    用户注册接口
    请求体: { "id_card_no": "身份证号", "student_id": "学号(可选)", "name": "张三", "password": "RSA加密后的密码(base64)", "department_id": 1 }
    注意：password 必须是使用 RSA 公钥加密后的 base64 字符串，请先调用 GET /api/auth/public-key 获取公钥
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    id_card_no = data.get('id_card_no')
    student_id = data.get('student_id')
    name = data.get('name')
    password = data.get('password')

    department_id = data.get('department_id')
    
    # 参数验证
    if not id_card_no or not name or not password:
        return jsonify({'error': '身份证号、姓名和密码不能为空'}), 400

    if not department_id:
        return jsonify({'error': 'department_id 不能为空'}), 400
    
    # 强制要求密码必须使用 RSA 加密，解密密码
    try:
        rsa_utils = get_rsa_utils()
        password = rsa_utils.decrypt_password(password)
    except ValueError as e:
        return jsonify({'error': f'密码解密失败，请确保密码已使用RSA公钥加密: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'密码处理失败: {str(e)}'}), 400
    
    # 基础格式校验（宽松）：身份证号 18位，前17位数字，最后一位数字或X/x
    id_card_no = str(id_card_no).strip()
    if len(id_card_no) != 18:
        return jsonify({'error': '身份证号必须为18位'}), 400
    if (not id_card_no[:17].isdigit()) or (not (id_card_no[17].isdigit() or id_card_no[17] in ('X', 'x'))):
        return jsonify({'error': '身份证号格式不正确'}), 400

    # 学号可选：如果提供，沿用原规则校验（12位纯数字）
    if student_id is not None and str(student_id).strip() != '':
        student_id = str(student_id).strip()
        if not student_id.isdigit():
            return jsonify({'error': '学号必须为纯数字'}), 400
        if len(student_id) != 12:
            return jsonify({'error': '学号必须为12位数字'}), 400
        # 学号唯一性检查（仅当填写时）
        if User.query.filter_by(student_id=student_id).first():
            return jsonify({'error': '该学号已注册'}), 400
    else:
        student_id = None

    # 检查身份证号是否已存在
    if User.query.filter_by(id_card_no=id_card_no).first():
        return jsonify({'error': '该身份证号已注册'}), 400
    
    # 仅支持直接传 department_id
    department = Department.query.get(department_id)
    if not department:
        return jsonify({'error': 'department_id 不存在'}), 400

    # 创建新用户
    user = User(
        id_card_no=id_card_no,
        student_id=student_id,
        name=name,
        department_id=department.id
    )
    user.set_password(password)
    
    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({
            'message': '注册成功',
            'user': user.to_dict(include_score=False)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'注册失败: {str(e)}'}), 500


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
    获取当前用户信息
    需要携带 JWT Token
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    return jsonify({
        'user': user.to_dict()
    }), 200

