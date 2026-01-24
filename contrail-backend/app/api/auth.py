"""
认证相关 API
提供登录、注册、Token 刷新等功能
"""
from flask import request, jsonify
from app.api import api_bp
from app.extensions import db
from app.models import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity


@api_bp.route('/auth/register', methods=['POST'])
def register():
    """
    用户注册接口
    请求体: { "student_id": "2021001", "name": "张三", "password": "123456", "class_info": "计算机1班" }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    student_id = data.get('student_id')
    name = data.get('name')
    password = data.get('password')
    class_info = data.get('class_info')
    
    # 参数验证
    if not student_id or not name or not password:
        return jsonify({'error': '学号、姓名和密码不能为空'}), 400
    
    # 检查学号是否已存在
    if User.query.filter_by(student_id=student_id).first():
        return jsonify({'error': '该学号已注册'}), 400
    
    # 创建新用户
    user = User(
        student_id=student_id,
        name=name,
        class_info=class_info
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
    请求体: { "student_id": "2021001", "password": "123456" }
    返回: { "access_token": "...", "user": {...} }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    student_id = data.get('student_id')
    password = data.get('password')
    
    if not student_id or not password:
        return jsonify({'error': '学号和密码不能为空'}), 400
    
    # 查找用户
    user = User.query.filter_by(student_id=student_id).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': '学号或密码错误'}), 401
    
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

