"""
学生核心业务 API
提供分数查询、积分变动记录等功能
"""
from flask import request, jsonify
from app.api import api_bp
from app.extensions import db
from app.models import User, ScoreLog, Comment, Certificate
from flask_jwt_extended import jwt_required, get_jwt_identity


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


@api_bp.route('/student/profile', methods=['GET'])
@jwt_required()
def get_student_profile():
    """
    获取当前登录学生的完整档案信息，用于小程序"个人详情页"
    返回包含基础信息、英语成绩、任职与获奖的完整数据
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': '用户不存在'}), 404

    # 获取用户基础信息
    user_dict = user.to_dict(include_score=True)
    
    # 从身份证号计算性别和出生日期
    id_card_no = user_dict.get('id_card_no', '')
    birth_date, gender = _extract_birth_and_gender(id_card_no)
    
    user_info = {
        'name': user_dict.get('name'),
        'student_id': user_dict.get('student_id'),
        'id_card_no': user_dict.get('id_card_no'),
        'phone': user_dict.get('phone'),
        'birthplace': user_dict.get('birthplace'),
        'ethnicity': user_dict.get('ethnicity'),
        'political_affiliation': user_dict.get('political_affiliation'),
        'gender': gender,  # 从身份证号计算得出
        'birth_date': birth_date,  # 从身份证号计算得出
        'college': user_dict.get('college'),
        'major': user_dict.get('major'),
        'grade': user_dict.get('grade'),
        'class_name': user_dict.get('class_name'),
        'credits': user_dict.get('credits'),
        'gpa': user_dict.get('gpa'),
        'base_score': user_dict.get('base_score'),
        'total_score': user_dict.get('total_score'),
    }

    # 获取该学生的所有证书（仅通过审核的，按上传时间倒序）
    certificates = user.certificates.filter_by(status=Certificate.STATUS_APPROVED)\
        .order_by(Certificate.upload_time.desc()).all()

    # 根据证书名称和类型分类处理
    cet4_cert = None
    cet6_cert = None
    ielts_certs = []  # 雅思可能有多个成绩
    position_certs = []  # 任职情况证书
    award_certs = []  # 获奖情况证书
    
    for cert in certificates:
        cert_name = cert.name or ''
        cert_name_upper = cert_name.upper()
        extra_data = cert.extra_data or {}
        if not isinstance(extra_data, dict):
            extra_data = {}
        
        cert_type = extra_data.get('type', '').lower() if isinstance(extra_data, dict) else ''
        
        # 根据证书名称和类型分类
        if cert_name == '英语四级' or ('CET-4' in cert_name_upper or '四级' in cert_name):
            if not cet4_cert:  # 只取第一个（最新的）
                cet4_cert = cert
        elif cert_name == '英语六级' or ('CET-6' in cert_name_upper or '六级' in cert_name):
            if not cet6_cert:  # 只取第一个（最新的）
                cet6_cert = cert
        elif 'IELTS' in cert_name_upper or '雅思' in cert_name:
            ielts_certs.append(cert)  # 收集所有雅思证书
        elif cert_name == '任职情况' or cert_name == '任职经历' or cert_type == 'position' or '任职' in cert_name:
            position_certs.append(cert)
        elif cert_name == '获奖情况' or cert_type in ['competition', 'honor']:
            award_certs.append(cert)
    
    # 构建英语成绩返回数据
    english_scores = {}
    
    # 处理四级（只有一个成绩，返回分数字符串）
    if cet4_cert:
        extra_data = cet4_cert.extra_data or {}
        if not isinstance(extra_data, dict):
            extra_data = {}
        score = extra_data.get('score')
        if score is not None:
            english_scores['cet4'] = str(score)
        else:
            english_scores['cet4'] = None
    else:
        english_scores['cet4'] = None
    
    # 处理六级（只有一个成绩，返回分数字符串）
    if cet6_cert:
        extra_data = cet6_cert.extra_data or {}
        if not isinstance(extra_data, dict):
            extra_data = {}
        score = extra_data.get('score')
        if score is not None:
            english_scores['cet6'] = str(score)
        else:
            english_scores['cet6'] = None
    else:
        english_scores['cet6'] = None
    
    # 处理雅思（可能有多个成绩，返回对象列表，包含总分及单项）
    ielts_scores = []
    for cert in ielts_certs:
        extra_data = cert.extra_data or {}
        if not isinstance(extra_data, dict):
            extra_data = {}
        
        # 检查是否有单项分（listening, reading, writing, speaking）
        has_components = any(key in extra_data for key in ['listening', 'reading', 'writing', 'speaking'])
        
        if has_components or 'total' in extra_data:
            ielts_record = {
                'date': extra_data.get('date'),
                'overall': str(extra_data.get('total') or ''),
                'listening': str(extra_data.get('listening') or ''),
                'reading': str(extra_data.get('reading') or ''),
                'writing': str(extra_data.get('writing') or ''),
                'speaking': str(extra_data.get('speaking') or '')
            }
            ielts_scores.append(ielts_record)
    
    english_scores['ielts'] = ielts_scores

    # 处理任职与获奖
    achievements = {
        'awards': [],
        'positions': []
    }
    
    # 处理任职情况（可能有多个任职记录）
    for cert in position_certs:
        extra_data = cert.extra_data or {}
        if not isinstance(extra_data, dict):
            extra_data = {}
        
        # 解析任职时间：优先使用 start_time/end_time，如果没有则尝试解析 date 字段
        start_time = extra_data.get('start_time')
        end_time = extra_data.get('end_time')
        
        # 如果 start_time/end_time 为空，尝试从 date 字段解析（格式：2023-09 至 2024-06）
        if not start_time and not end_time:
            date_str = extra_data.get('date', '') or ''
            if date_str and '至' in date_str:
                parts = date_str.split('至')
                if len(parts) == 2:
                    start_time = parts[0].strip()
                    end_time = parts[1].strip()
        
        # 标准化任职信息
        position_info = {
            'start_time': start_time,
            'end_time': end_time,
            'organization': extra_data.get('organization') or extra_data.get('org'),
            'role': extra_data.get('role') or extra_data.get('position'),
            'level': extra_data.get('level'),
            'collective_awards': []
        }
        
        # 处理集体奖项：优先使用 collective_awards/collectiveAwards，如果没有则使用 award 字段
        collective_awards = extra_data.get('collective_awards') or extra_data.get('collectiveAwards')
        if not collective_awards:
            collective_awards = extra_data.get('award', '')  # 兼容 award 字段
        
        if collective_awards:
            if isinstance(collective_awards, list):
                position_info['collective_awards'] = collective_awards
            elif isinstance(collective_awards, str):
                # 如果是字符串，检查是否为空或"无"
                if collective_awards.strip() and collective_awards.strip() != '无':
                    position_info['collective_awards'] = [collective_awards.strip()]
        
        achievements['positions'].append(position_info)
    
    # 处理获奖情况（可能有多个获奖记录）
    for cert in award_certs:
        extra_data = cert.extra_data or {}
        if not isinstance(extra_data, dict):
            extra_data = {}
        
        # 标准化获奖信息
        award_info = {
            'date': extra_data.get('date'),
            'name': extra_data.get('name') or cert.name,  # 奖励名称，如果没有 name，使用证书名称
            'level': extra_data.get('level'),  # 奖励级别
            'rank': extra_data.get('rank'),  # 获奖等次
            'organizer': extra_data.get('organizer'),  # 主办单位
            'grade': extra_data.get('grade') or extra_data.get('award'),  # 兼容旧数据
            'type': extra_data.get('type') or extra_data.get('category')
        }
        
        achievements['awards'].append(award_info)

    return jsonify({
        'user_info': user_info,
        'english_scores': english_scores,
        'achievements': achievements
    }), 200


