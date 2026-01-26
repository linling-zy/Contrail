"""
学生核心业务 API
提供分数查询、积分变动记录等功能
"""
from flask import request, jsonify
from app.api import api_bp
from app.extensions import db
from app.models import User, ScoreLog, Comment
from flask_jwt_extended import jwt_required, get_jwt_identity


@api_bp.route('/student/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """
    主页仪表盘（给小程序 pages/index 使用）
    返回:
    {
      "score": 85,
      "comment": "....",
      "process_status": {
        "preliminary": "qualified|pending|unqualified",
        "medical": "qualified|pending|unqualified",
        "political": "qualified|pending|unqualified",
        "admission": "qualified|pending|unqualified"
      }
    }

    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': '用户不存在'}), 404

    # 获取最新的一条评语（按创建时间倒序）
    latest_comment = Comment.query.filter_by(user_id=user_id)\
        .order_by(Comment.create_time.desc())\
        .first()
    
    comment_content = latest_comment.content if latest_comment else ""

    payload = {
        "score": user.total_score,
        "comment": comment_content,
        "process_status": {
            "preliminary": user.preliminary_status,
            "medical": user.medical_status,
            "political": user.political_status,
            "admission": user.admission_status,
        }
    }
    return jsonify(payload), 200


@api_bp.route('/student/score', methods=['GET'])
@jwt_required()
def get_score():
    """
    获取当前用户的积分信息
    返回: { "base_score": 80, "total_score": 85, "score_logs": [...] }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 获取积分流水记录（最近50条）
    score_logs = ScoreLog.query.filter_by(user_id=user_id)\
        .order_by(ScoreLog.create_time.desc())\
        .limit(50)\
        .all()
    
    return jsonify({
        'base_score': user.base_score,
        'total_score': user.total_score,
        'score_logs': [log.to_dict() for log in score_logs]
    }), 200


@api_bp.route('/student/score/history', methods=['GET'])
@jwt_required()
def get_score_history():
    """
    获取积分变动历史记录（支持分页）
    查询参数: page (页码, 默认1), per_page (每页数量, 默认20)
    """
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 分页查询
    pagination = ScoreLog.query.filter_by(user_id=user_id)\
        .order_by(ScoreLog.create_time.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages,
        'items': [log.to_dict() for log in pagination.items]
    }), 200


