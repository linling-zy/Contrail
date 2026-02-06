"""
管理员学生管理 API
提供学生列表查询、状态更新、批量注册等功能
需要管理员权限，普通管理员只能管理自己部门的学生

依赖项：
- pandas: 用于解析 Excel 文件（pip install pandas openpyxl）
- openpyxl: pandas 读取 Excel 文件所需的引擎（pip install openpyxl）
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
from app.utils.admin_permission import admin_required
from app.utils.s3_presign import presign_get_object_url
from flask_jwt_extended import jwt_required, get_jwt_identity
from docxtpl import DocxTemplate

# 尝试导入 pandas，如果未安装会抛出 ImportError
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


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


def _cleanup_old_export_files(app, max_age_minutes=30):
    """
    清理临时目录中超过指定时间的导出文件
    
    Args:
        app: Flask 应用实例
        max_age_minutes: 文件最大保留时间（分钟），默认30分钟
    """
    try:
        temp_dir = os.path.join(app.instance_path, 'temp')
        if not os.path.exists(temp_dir):
            return
        
        current_time = datetime.now().timestamp()
        max_age_seconds = max_age_minutes * 60
        
        for filename in os.listdir(temp_dir):
            if filename.startswith('export_') and filename.endswith('.zip'):
                file_path = os.path.join(temp_dir, filename)
                try:
                    # 获取文件修改时间
                    file_mtime = os.path.getmtime(file_path)
                    age_seconds = current_time - file_mtime
                    
                    # 如果文件超过指定时间，删除它
                    if age_seconds > max_age_seconds:
                        os.remove(file_path)
                except (OSError, FileNotFoundError):
                    # 文件可能已被删除或无法访问，忽略错误
                    pass
    except Exception:
        # 清理失败不影响主流程，静默失败
        pass


def _run_department_export_task(app, task_id: str, admin_id: int, dept_id: int):
    """
    后台线程：部门学生档案批量导出（单人双文件：Word+Excel）

    步骤：
      1. 查询部门和学生（预加载 certificates 和 score_logs）
      2. 遍历学生，提取证书数据（从 extra_data JSON）
      3. 生成积分明细 Excel 文件
      4. 生成送飞鉴定表 Word 文件
      5. 将所有文档打包为 ZIP 文件（按 {学院}_{班级}_{姓名}_{学号}/ 结构）
      6. 更新 EXPORT_TASKS 中的任务状态
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
            # 注意：User.certificates 和 User.score_logs 使用 lazy='dynamic'，返回 Query 对象
            # 不能使用 joinedload，需要在循环中直接访问（dynamic 关系本身就是 Query 对象）
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

            # 检查 pandas 是否可用
            if not PANDAS_AVAILABLE:
                with EXPORT_TASKS_LOCK:
                    task = EXPORT_TASKS.get(task_id)
                    if task is not None:
                        task.update({
                            'status': 'failed',
                            'error': 'pandas 未安装，无法生成 Excel 文件',
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
                    # ========== 1. 数据清洗与提取 ==========
                    birth_date, gender = _extract_birth_and_gender(user.id_card_no)
                    dept = user.department or department
                    
                    # 获取审核通过的证书
                    # 注意：user.certificates 是 dynamic 关系，返回 Query 对象，需要调用 .all() 或 .filter()
                    approved_certs = user.certificates.filter_by(status=Certificate.STATUS_APPROVED).all()
                    
                    # 提取英语四六级成绩（与 student.py 的 profile 接口保持一致）
                    cet4_cert = None
                    cet6_cert = None
                    for cert in approved_certs:
                        cert_name = cert.name or ''
                        cert_name_upper = cert_name.upper()
                        
                        # 根据证书名称分类（与 profile 接口逻辑一致）
                        if cert_name == '英语四级' or ('CET-4' in cert_name_upper or '四级' in cert_name):
                            if not cet4_cert:  # 只取第一个（最新的）
                                cet4_cert = cert
                        elif cert_name == '英语六级' or ('CET-6' in cert_name_upper or '六级' in cert_name):
                            if not cet6_cert:  # 只取第一个（最新的）
                                cet6_cert = cert
                    
                    # 处理四级（与 profile 接口逻辑一致）
                    cet4_score = ''
                    if cet4_cert:
                        extra_data = cet4_cert.extra_data or {}
                        if not isinstance(extra_data, dict):
                            extra_data = {}
                        score = extra_data.get('score')
                        if score is not None:
                            cet4_score = str(score)
                    
                    # 处理六级（与 profile 接口逻辑一致）
                    cet6_score = ''
                    if cet6_cert:
                        extra_data = cet6_cert.extra_data or {}
                        if not isinstance(extra_data, dict):
                            extra_data = {}
                        score = extra_data.get('score')
                        if score is not None:
                            cet6_score = str(score)
                    
                    # 提取雅思成绩（取最新的一条）
                    ielts_l = ielts_r = ielts_w = ielts_s = ielts_total = ''
                    ielts_certs = [cert for cert in approved_certs 
                                  if 'IELTS' in (cert.name or '').upper() or '雅思' in (cert.name or '')]
                    if ielts_certs:
                        # 按 upload_time 排序，取最新的
                        latest_ielts = max(ielts_certs, key=lambda c: c.upload_time or datetime.min)
                        extra_data = latest_ielts.extra_data or {}
                        if isinstance(extra_data, dict):
                            # 确保空值转换为空字符串，而不是 'None'
                            listening_val = extra_data.get('listening')
                            reading_val = extra_data.get('reading')
                            writing_val = extra_data.get('writing')
                            speaking_val = extra_data.get('speaking')
                            total_val = extra_data.get('total')
                            
                            ielts_l = str(listening_val) if listening_val is not None else ''
                            ielts_r = str(reading_val) if reading_val is not None else ''
                            ielts_w = str(writing_val) if writing_val is not None else ''
                            ielts_s = str(speaking_val) if speaking_val is not None else ''
                            ielts_total = str(total_val) if total_val is not None else ''
                    
                    # 提取任职情况
                    # 先识别任职类证书（根据证书名称和类型，与 student.py 保持一致）
                    position_certs = []
                    for cert in approved_certs:
                        cert_name = cert.name or ''
                        cert_type = (cert.extra_data or {}).get('type', '').lower() if isinstance(cert.extra_data, dict) else ''
                        if cert_name == '任职情况' or cert_name == '任职经历' or cert_type == 'position' or '任职' in cert_name:
                            position_certs.append(cert)
                    
                    jobs = []
                    for cert in position_certs:
                        extra_data = cert.extra_data or {}
                        if not isinstance(extra_data, dict):
                            extra_data = {}
                        
                        # 解析任职时间：优先使用 start_time/end_time，如果没有则尝试解析 date 字段
                        start_time = extra_data.get('start_time', '') or ''
                        end_time = extra_data.get('end_time', '') or ''
                        
                        # 如果 start_time/end_time 为空，尝试从 date 字段解析（格式：2026-02 至 2026-02）
                        if not start_time and not end_time:
                            date_str = extra_data.get('date', '') or ''
                            if date_str and '至' in date_str:
                                parts = date_str.split('至')
                                if len(parts) == 2:
                                    start_time = parts[0].strip()
                                    end_time = parts[1].strip()
                        
                        # 处理集体获奖情况：优先使用 collective_awards，如果没有则使用 award 字段（与 student.py 保持一致）
                        collective_awards = extra_data.get('collective_awards') or extra_data.get('collectiveAwards')
                        if not collective_awards:
                            collective_awards = extra_data.get('award', '')  # 兼容 award 字段
                        
                        collective_awards_str = ''
                        if collective_awards:
                            if isinstance(collective_awards, list):
                                collective_awards_str = '；'.join(str(a) for a in collective_awards if a)
                            elif isinstance(collective_awards, str):
                                collective_awards_str = collective_awards.strip()
                        
                        job = {
                            'start_time': start_time,
                            'end_time': end_time,
                            'role': extra_data.get('role') or extra_data.get('position', ''),  # 兼容 position 字段
                            'organization': extra_data.get('organization') or extra_data.get('org', ''),  # 兼容 org 字段
                            'collective_awards': collective_awards_str,
                        }
                        jobs.append(job)
                    
                    # 提取获奖情况（先识别获奖类证书，与 student.py 保持一致）
                    award_certs = []
                    for cert in approved_certs:
                        cert_name = cert.name or ''
                        cert_type = (cert.extra_data or {}).get('type', '').lower() if isinstance(cert.extra_data, dict) else ''
                        # 排除英语和任职类证书
                        is_english = (cert_name == '英语四级' or cert_name == '英语六级' or 
                                     'CET-4' in cert_name.upper() or 'CET-6' in cert_name.upper() or
                                     '四级' in cert_name or '六级' in cert_name or
                                     'IELTS' in cert_name.upper() or '雅思' in cert_name)
                        is_position = (cert_name == '任职情况' or cert_name == '任职经历' or 
                                      cert_type == 'position' or '任职' in cert_name)
                        
                        # 识别获奖类证书
                        if not is_english and not is_position:
                            if cert_name == '获奖情况' or cert_type in ['competition', 'honor']:
                                award_certs.append(cert)
                            # 如果证书名称不是明确的英语/任职类，也视为获奖（兼容处理）
                            elif cert_name and cert_name not in ['英语四级', '英语六级', '任职情况', '任职经历']:
                                award_certs.append(cert)
                    
                    awards = []
                    for cert in award_certs:
                        extra_data = cert.extra_data or {}
                        if not isinstance(extra_data, dict):
                            extra_data = {}
                        
                        # 标准化获奖信息（与 profile 接口逻辑一致）
                        award_date = extra_data.get('date')
                        # 如果 date 为空，尝试使用 upload_time
                        if not award_date and cert.upload_time:
                            award_date = cert.upload_time.strftime('%Y-%m-%d')
                        
                        award = {
                            'date': award_date if award_date else '',  # 转换为字符串或空字符串
                            'name': extra_data.get('name') or cert.name or '',  # 奖励名称，如果没有 name，使用证书名称
                            'level': extra_data.get('level') or '',  # 奖励级别
                            'rank': extra_data.get('rank') or '',  # 获奖等次
                            'organizer': extra_data.get('organizer') or '',  # 主办单位
                        }
                        
                        awards.append(award)
                    
                    # ========== 2. 生成积分明细 Excel ==========
                    # 注意：user.score_logs 是 dynamic 关系，返回 Query 对象
                    score_logs_list = user.score_logs.order_by(ScoreLog.create_time.asc()).all()
                    excel_data = []
                    for log in score_logs_list:
                        if log.delta is None:
                            continue
                        date_str = log.create_time.strftime('%Y-%m-%d') if log.create_time else ''
                        delta_str = f"+{log.delta}" if log.delta > 0 else str(log.delta)
                        reason = log.reason or ''
                        # 操作类型映射：'system' -> '系统', 'manual' -> '人工'
                        op_type = '系统' if log.type == ScoreLog.TYPE_SYSTEM else '人工'
                        excel_data.append({
                            '日期': date_str,
                            '变动分值': delta_str,
                            '变动原因': reason,
                            '操作类型': op_type,
                        })
                    
                    # 使用 pandas 生成 Excel
                    df = pd.DataFrame(excel_data)
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='积分明细')
                    excel_buffer.seek(0)
                    
                    # ========== 3. 准备 Word Context（包含定长切片逻辑）==========
                    # 任职情况：前3条映射到扁平变量，超出部分放入 jobs_extra
                    jobs_main = jobs[:3]
                    jobs_extra_raw = jobs[3:]
                    # 格式化额外任职情况：任职时间：xxx，担任职务：xxx，任职期间集体获奖情况：xxxxxx;
                    # 注意：docxtpl 模板中可能使用 {% for job in jobs_extra %} 循环，需要传递字典列表
                    jobs_extra = []
                    for idx, job in enumerate(jobs_extra_raw, start=4):  # 从第4条开始编号
                        start_time = job.get('start_time', '') or ''
                        end_time = job.get('end_time', '') or ''
                        job_time = f"{start_time} - {end_time}".strip(' -') if (start_time or end_time) else '无'
                        job_role = job.get('role', '') or '无'
                        collective_awards = job.get('collective_awards', '') or '无'
                        # 格式：任职时间：xxx，担任职务：xxx，任职期间集体获奖情况：xxxxxx;
                        job_str = f"任职时间：{job_time}，担任职务：{job_role}，任职期间集体获奖情况：{collective_awards};"
                        jobs_extra.append({
                            'index': idx,
                            'text': job_str,
                            'time': job_time,
                            'role': job_role,
                            'collective_awards': collective_awards
                        })
                    
                    # 填充前3条任职变量（不足3条用空字符串填充）
                    job_vars = {}
                    for i in range(1, 4):
                        if i <= len(jobs_main):
                            job = jobs_main[i - 1]
                            start_time = job.get('start_time', '') or ''
                            end_time = job.get('end_time', '') or ''
                            # 如果任职时间都为空，显示"无"，否则显示时间范围
                            if start_time or end_time:
                                job_vars[f'job_{i}_time'] = f"{start_time} - {end_time}".strip(' -')
                            else:
                                job_vars[f'job_{i}_time'] = '无'
                            job_vars[f'job_{i}_role'] = job.get('role', '') or ''
                            # 任职期间集体获奖情况：Word 模板使用 job_{i}_note 字段
                            # 如果为空，显示"无"
                            collective_awards = job.get('collective_awards', '') or ''
                            job_vars[f'job_{i}_note'] = collective_awards if collective_awards else '无'
                            # 保留兼容变量名
                            job_vars[f'job_{i}_collective_awards'] = collective_awards if collective_awards else '无'
                        else:
                            job_vars[f'job_{i}_time'] = ''
                            job_vars[f'job_{i}_role'] = ''
                            job_vars[f'job_{i}_note'] = ''
                            job_vars[f'job_{i}_collective_awards'] = ''
                    
                    # 获奖情况：前3条映射到扁平变量，超出部分放入 awards_extra
                    awards_main = awards[:3]
                    awards_extra_raw = awards[3:]
                    # 格式化额外获奖情况：奖励时间：xxx，奖励名称：xxxx，主办单位：xxx；奖励级别：xxxx，获奖等次：xxx；
                    # 注意：docxtpl 模板中可能使用 {% for award in awards_extra %} 循环，需要传递字典列表
                    awards_extra = []
                    for idx, award in enumerate(awards_extra_raw, start=4):  # 从第4条开始编号
                        award_date = award.get('date', '') or '无'
                        award_name = award.get('name', '') or '无'
                        award_organizer = award.get('organizer', '') or '无'
                        award_level = award.get('level', '') or '无'
                        award_rank = award.get('rank', '') or '无'
                        # 格式：奖励时间：xxx，奖励名称：xxxx，主办单位：xxx；奖励级别：xxxx，获奖等次：xxx；
                        award_str = f"奖励时间：{award_date}，奖励名称：{award_name}，主办单位：{award_organizer}；奖励级别：{award_level}，获奖等次：{award_rank}；"
                        awards_extra.append({
                            'index': idx,
                            'text': award_str,
                            'date': award_date,
                            'name': award_name,
                            'organizer': award_organizer,
                            'level': award_level,
                            'rank': award_rank
                        })
                    
                    # 填充前3条获奖变量（不足3条用空字符串填充）
                    # 注意：Word 模板使用的字段名为：award_{i}_time, award_{i}_name, award_{i}_host, award_{i}_level, award_{i}_grade
                    award_vars = {}
                    for i in range(1, 4):
                        if i <= len(awards_main):
                            award = awards_main[i - 1]
                            # 确保所有字段都不为 None，转换为字符串
                            award_name = award.get('name', '') or ''
                            award_date = award.get('date', '') or ''
                            award_level = award.get('level', '') or ''
                            award_rank = award.get('rank', '') or ''  # rank 对应模板中的 grade
                            award_organizer = award.get('organizer', '') or ''  # organizer 对应模板中的 host
                            
                            # Word 模板使用的字段名
                            award_vars[f'award_{i}_time'] = str(award_date) if award_date else ''
                            award_vars[f'award_{i}_name'] = str(award_name) if award_name else ''
                            award_vars[f'award_{i}_host'] = str(award_organizer) if award_organizer else ''  # 主办单位
                            award_vars[f'award_{i}_level'] = str(award_level) if award_level else ''
                            award_vars[f'award_{i}_grade'] = str(award_rank) if award_rank else ''  # 获奖等次
                            
                            # 保留兼容变量名
                            award_vars[f'award_{i}_date'] = str(award_date) if award_date else ''
                            award_vars[f'award_{i}_rank'] = str(award_rank) if award_rank else ''
                            award_vars[f'award_{i}_organizer'] = str(award_organizer) if award_organizer else ''
                        else:
                            award_vars[f'award_{i}_time'] = ''
                            award_vars[f'award_{i}_name'] = ''
                            award_vars[f'award_{i}_host'] = ''
                            award_vars[f'award_{i}_level'] = ''
                            award_vars[f'award_{i}_grade'] = ''
                            # 保留兼容变量名
                            award_vars[f'award_{i}_date'] = ''
                            award_vars[f'award_{i}_rank'] = ''
                            award_vars[f'award_{i}_organizer'] = ''
                    
                    # 生成导出日期
                    export_date = datetime.now().strftime('%Y年%m月%d日')
                    
                    # 合并显示英语四六级分数（格式：四级：xxx\n六级：xxx，如果没有就写"无"）
                    english_level = ''
                    if cet4_score or cet6_score:
                        parts = []
                        if cet4_score:
                            parts.append(f'四级：{cet4_score}')
                        else:
                            parts.append('四级：无')
                        if cet6_score:
                            parts.append(f'六级：{cet6_score}')
                        else:
                            parts.append('六级：无')
                        english_level = '\n'.join(parts)
                    else:
                        english_level = '四级：无\n六级：无'
                    
                    # 格式化 GPA（保留2位小数）
                    gpa_display = ''
                    if user.gpa is not None:
                        gpa_display = f'{user.gpa:.2f}'
                    
                    # 构建 Word 模板上下文
                    context = {
                        'name': user.name or '',
                        'id_card_no': user.id_card_no or '',
                        'student_id': user.student_id or '',
                        'college': dept.college or '',
                        'class_name': dept.class_name or '',  # 班级
                        'grade': dept.grade or '',
                        'total_score': user.total_score or 0,
                        'birth_date': birth_date,
                        'gender': gender,
                        'ethnicity': user.ethnicity or '',  # 民族
                        'political_affiliation': user.political_affiliation or '',  # 政治面貌
                        'gpa': gpa_display,  # 学分绩点
                        'birthplace': user.birthplace or '',  # 籍贯
                        'phone': user.phone or '',  # 联系电话
                        'export_date': export_date,
                        # 英语成绩（Word 模板使用 english_level 字段）
                        'english_level': english_level,  # 格式：四级：xxx\n六级：xxx，如果没有就写"无"
                        # 保留兼容变量名
                        'cet4_score': cet4_score,
                        'cet6_score': cet6_score,
                        'cet_scores': english_level,
                        'cet4': cet4_score,
                        'cet6': cet6_score,
                        # 雅思成绩（Word 模板使用的字段名）
                        'ielts_speaking': ielts_s,  # 口语
                        'ielts_listening': ielts_l,  # 听力
                        'ielts_reading': ielts_r,  # 阅读
                        'ielts_writing': ielts_w,  # 写作
                        'ielts_total': ielts_total,  # 总分
                        # 保留兼容变量名
                        'ielts_l': ielts_l,
                        'ielts_r': ielts_r,
                        'ielts_w': ielts_w,
                        'ielts_s': ielts_s,
                        # 任职情况（前3条）
                        **job_vars,
                        'jobs_extra': jobs_extra,  # 超出3条的数据，用于附录页循环展示（格式化的字典列表）
                        # 获奖情况（前3条）
                        **award_vars,
                        'awards_extra': awards_extra,  # 超出3条的数据，用于附录页循环展示（格式化的字典列表）
                        # 缺失字段（必须置空）
                        'photo_path': None,
                        'warning_logs': [],  # 积分预警情况（暂无数据源，保持为空）
                    }
                    
                    # #region agent log
                    import json
                    log_data = {
                        'sessionId': 'debug-session',
                        'runId': 'run1',
                        'hypothesisId': 'J',
                        'location': 'admin_student.py:560',
                        'message': '检查额外数据格式',
                        'data': {
                            'user_id': user.id,
                            'jobs_extra_count': len(jobs_extra),
                            'jobs_extra_sample': jobs_extra[0] if jobs_extra else None,
                            'awards_extra_count': len(awards_extra),
                            'awards_extra_sample': awards_extra[0] if awards_extra else None
                        },
                        'timestamp': int(datetime.now().timestamp() * 1000)
                    }
                    try:
                        with open(r'e:\01_Work_Study\Contrail\.cursor\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                    except Exception:
                        pass
                    # #endregion agent log
                    
                    # ========== 4. 生成 Word 文档 ==========
                    doc = DocxTemplate(template_path)
                    doc.render(context)
                    word_buffer = io.BytesIO()
                    doc.save(word_buffer)
                    word_buffer.seek(0)
                    
                    # ========== 5. 构建 ZIP 文件结构 ==========
                    # 文件夹名：{学院}_{班级}_{姓名}_{学号}
                    safe_name = (user.name or '未命名').replace('/', '_').replace('\\', '_')
                    safe_college = (dept.college or '未知学院').replace('/', '_').replace('\\', '_')
                    safe_class = (dept.class_name or f'班级{dept.id}').replace('/', '_').replace('\\', '_')
                    stu_id_or_id = user.student_id or user.id_card_no or ''
                    folder_name = f'{safe_college}_{safe_class}_{safe_name}_{stu_id_or_id}'
                    
                    # Excel 文件名：{姓名}_积分明细.xlsx
                    excel_filename = f'{safe_name}_积分明细.xlsx'
                    excel_path_in_zip = f'{folder_name}/{excel_filename}'
                    
                    # Word 文件名：{姓名}_送飞鉴定表.docx
                    word_filename = f'{safe_name}_送飞鉴定表.docx'
                    word_path_in_zip = f'{folder_name}/{word_filename}'
                    
                    # 写入 ZIP
                    zipf.writestr(excel_path_in_zip, excel_buffer.getvalue())
                    zipf.writestr(word_path_in_zip, word_buffer.getvalue())
                    
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
        - department_id: 按班级/部门ID过滤（可选）
        - status_stage: 按阶段状态过滤，可选值：preliminary/medical/political/admission（可选）
        - status_value: 按状态值过滤，可选值：pending/qualified/unqualified（可选，需配合status_stage使用）
    返回: { "total": n, "page": 1, "per_page": 20, "pages": n, "items": [...] }
    
    注意：
    - 权限控制：普通管理员只能查询其管理的部门下的学生（已通过get_admin_accessible_query实现）
    - department_id过滤会进一步限制在指定部门，但必须确保该部门在管理员权限范围内
    """
    admin_id = get_jwt_identity()
    admin = AdminUser.query.get(admin_id)
    
    if not admin:
        return jsonify({'error': '管理员不存在'}), 404
    
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    filter_type = request.args.get('filter')  # name/student_id/class_name
    keyword = request.args.get('keyword', '').strip()
    department_id = request.args.get('department_id', type=int)  # 部门ID过滤
    status_stage = request.args.get('status_stage')  # 阶段名称
    status_value = request.args.get('status_value')  # 状态值
    
    # 参数验证
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20
    
    # 获取基础查询（已根据权限过滤）
    query = get_admin_accessible_query(User, admin_id)
    
    # 部门ID过滤
    if department_id is not None:
        # 检查管理员是否有权限访问该部门
        if admin.role != AdminUser.ROLE_SUPER:
            # 普通管理员需要检查该部门是否在其管理范围内
            managed_dept_ids = [dept.id for dept in admin.managed_departments.all()]
            if department_id not in managed_dept_ids:
                return jsonify({'error': '无权访问该部门'}), 403
        
        # 验证部门是否存在
        department = Department.query.get(department_id)
        if not department:
            return jsonify({'error': '部门不存在'}), 404
        
        query = query.filter(User.department_id == department_id)
    
    # 阶段状态过滤
    if status_stage:
        if status_stage not in VALID_STAGES:
            return jsonify({
                'error': f'无效的阶段名称: {status_stage}，支持的值: {", ".join(VALID_STAGES)}'
            }), 400
        
        if status_value:
            if status_value not in VALID_STATUSES:
                return jsonify({
                    'error': f'无效的状态值: {status_value}，支持的值: {", ".join(VALID_STATUSES)}'
                }), 400
            
            # 根据阶段和状态值过滤
            if status_stage == 'preliminary':
                query = query.filter(User.preliminary_status == status_value)
            elif status_stage == 'medical':
                query = query.filter(User.medical_status == status_value)
            elif status_stage == 'political':
                query = query.filter(User.political_status == status_value)
            elif status_stage == 'admission':
                query = query.filter(User.admission_status == status_value)
    
    # 关键词搜索（保留原有功能）
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
    返回: { "student": {...}, "comments": [...], "certificates": [...] }
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
    
    # 获取评语列表（按创建时间倒序）
    comments = student.comments.order_by(Comment.create_time.desc()).all()
    comments_list = [comment.to_dict() for comment in comments]
    
    # 获取证书列表（按上传时间倒序）
    certificates = student.certificates.order_by(Certificate.upload_time.desc()).all()
    certificates_list = []
    for cert in certificates:
        cert_dict = cert.to_dict()
        # 添加前端需要的字段
        cert_dict['certName'] = cert.name
        # 生成 Presigned URL
        cert_dict['imgUrl'] = presign_get_object_url(cert.image_url)
        certificates_list.append(cert_dict)
    
    return jsonify({
        'student': student_dict,
        'comments': comments_list,
        'certificates': certificates_list
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
            download_url = url_for('admin.download_export_file', task_id=task_id)

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
    # 清理超过30分钟的旧文件
    _cleanup_old_export_files(current_app, max_age_minutes=30)
    
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
            
            # 创建新用户，使用部门的基础分
            user = User(
                id_card_no=id_card_no,
                student_id=student_id,
                name=name,
                department_id=department.id,
                base_score=department.base_score  # 使用部门的基础分
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


@admin_bp.route('/students/<int:student_id>/score-logs', methods=['GET'])
@admin_required
def get_student_score_logs(student_id):
    """
    获取学生积分流水记录（管理员权限）
    查询参数:
        - page: 页码（默认1）
        - limit: 每页数量（默认20）
        - type: 类型过滤（1-人工调整, 2-系统自动）
    返回: {
        "code": 200,
        "data": {
            "items": [...],
            "total": 100
        },
        "message": "success"
    }
    """
    admin_id = get_jwt_identity()
    
    # 检查权限
    has_access, student = check_admin_access_to_student(admin_id, student_id)
    
    if not student:
        return jsonify({'code': 404, 'message': '学生不存在'}), 404
    
    if not has_access:
        return jsonify({'code': 403, 'message': '无权访问该学生信息'}), 403
    
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    type_filter = request.args.get('type', type=int)  # 1-人工, 2-系统
    
    # 参数验证
    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 20
    
    # 构建查询
    query = ScoreLog.query.filter_by(user_id=student_id)
    
    # 类型过滤
    if type_filter is not None:
        if type_filter == 1:
            query = query.filter(ScoreLog.type == ScoreLog.TYPE_MANUAL)
        elif type_filter == 2:
            query = query.filter(ScoreLog.type == ScoreLog.TYPE_SYSTEM)
        else:
            return jsonify({'code': 400, 'message': '无效的类型参数，支持的值：1（人工调整）或 2（系统自动）'}), 400
    
    # 按创建时间倒序排列
    query = query.order_by(ScoreLog.create_time.desc())
    
    # 分页查询
    pagination = query.paginate(
        page=page,
        per_page=limit,
        error_out=False
    )
    
    # 为了计算 old_score 和 new_score，需要获取所有记录（按时间正序）
    # 注意：即使使用了类型过滤，old_score 的计算也应该基于所有记录，而不是只考虑过滤后的记录
    # 这样才能保证 old_score 的准确性（反映该记录发生前的实际总分）
    
    # 获取基础分
    base_score = student.base_score
    
    # 获取所有记录（用于计算分数，按时间正序，不考虑类型过滤）
    all_logs = ScoreLog.query.filter_by(user_id=student_id)\
        .order_by(ScoreLog.create_time.asc()).all()
    
    # 构建一个字典，key为log_id，value为该记录之前的累计分数
    score_before_log = {}
    current_score = base_score
    for log in all_logs:
        score_before_log[log.id] = current_score
        current_score += log.delta
    
    # 构建返回数据
    items = []
    for log in pagination.items:
        # 计算变动前后的分数
        old_score = score_before_log.get(log.id, base_score)
        new_score = old_score + log.delta
        
        # 类型转换：'manual' -> 1, 'system' -> 2
        type_value = 1 if log.type == ScoreLog.TYPE_MANUAL else 2
        
        # 操作人姓名：如果是系统操作，返回"系统"；如果是人工操作，由于没有operator_id字段，返回"管理员"
        operator_name = "系统" if log.type == ScoreLog.TYPE_SYSTEM else "管理员"
        
        items.append({
            'id': log.id,
            'old_score': old_score,
            'new_score': new_score,
            'change_amount': log.delta,
            'reason': log.reason or '',
            'type': type_value,
            'create_time': log.create_time.isoformat() if log.create_time else None,
            'operator_name': operator_name
        })
    
    return jsonify({
        'code': 200,
        'data': {
            'items': items,
            'total': pagination.total
        },
        'message': 'success'
    }), 200


@admin_bp.route('/students/<int:student_id>/archive', methods=['PUT'])
@admin_required
def update_student_archive(student_id):
    """
    一次性更新学生档案完整信息（管理员权限）
    包含：基本资料、四阶段进度、教师评价
    
    请求体: {
        "base_info": {
            "name": "张三",
            "student_id": "2023001",
            "department_id": 1,
            "base_score": 80
            // 其他可更新字段...
        },
        "process_status": {
            "preliminary": "qualified",  // preliminary/medical/political/admission
            "medical": "pending",
            "political": "unqualified",
            "admission": "pending"
        },
        "new_comment": "该生在校期间表现优秀..."  // 可选，如果有内容则新增评语
    }
    返回: {
        "code": 200,
        "message": "档案更新成功"
    }
    
    注意：
    - 所有更新在一个事务中完成，确保原子性
    - 四个阶段状态字段直接更新到 User 表中（不存在独立的 StudentProcess 表）
    - 如果 new_comment 不为空，会新增一条 Comment 记录，关联当前管理员
    """
    admin_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400
    
    # 检查权限
    has_access, student = check_admin_access_to_student(admin_id, student_id)
    
    if not student:
        return jsonify({'code': 404, 'message': '学生不存在'}), 404
    
    if not has_access:
        return jsonify({'code': 403, 'message': '无权操作该学生'}), 403
    
    # 获取管理员信息（用于评语作者）
    admin = AdminUser.query.get(admin_id)
    if not admin:
        return jsonify({'code': 404, 'message': '管理员不存在'}), 404
    
    # 开始事务
    try:
        # 1. 更新学生基本信息
        base_info = data.get('base_info', {})
        if base_info:
            # 可更新的基础字段
            if 'name' in base_info:
                student.name = base_info['name']

            if 'student_id' in base_info:
                # 学号唯一性检查（如果修改了学号）
                new_student_id = base_info['student_id']
                if new_student_id and new_student_id != student.student_id:
                    # 检查新学号是否已被其他学生使用
                    existing_user = User.query.filter_by(student_id=new_student_id).first()
                    if existing_user and existing_user.id != student_id:
                        return jsonify({'code': 400, 'message': f'学号 {new_student_id} 已被其他学生使用'}), 400
                student.student_id = new_student_id

            if 'department_id' in base_info:
                dept_id = base_info['department_id']
                # 验证部门是否存在
                if dept_id is not None:
                    department = Department.query.get(dept_id)
                    if not department:
                        return jsonify({'code': 404, 'message': f'部门ID {dept_id} 不存在'}), 404
                    # 普通管理员只能将学生分配到其管理的部门
                    if admin.role != AdminUser.ROLE_SUPER:
                        managed_dept_ids = [dept.id for dept in admin.managed_departments.all()]
                        if dept_id not in managed_dept_ids:
                            return jsonify({'code': 403, 'message': '无权将学生分配到该部门'}), 403
                student.department_id = dept_id

            if 'base_score' in base_info:
                base_score = base_info['base_score']
                if not isinstance(base_score, int):
                    return jsonify({'code': 400, 'message': 'base_score 必须是整数'}), 400
                student.base_score = base_score

            # 学分 / 绩点 / 籍贯 / 联系电话等补充信息
            if 'credits' in base_info:
                value = base_info['credits']
                if value is None or value == '':
                    student.credits = None
                else:
                    try:
                        student.credits = float(value)
                    except (TypeError, ValueError):
                        return jsonify({'code': 400, 'message': 'credits 必须是数字'}), 400

            if 'gpa' in base_info:
                value = base_info['gpa']
                if value is None or value == '':
                    student.gpa = None
                else:
                    try:
                        gpa = float(value)
                    except (TypeError, ValueError):
                        return jsonify({'code': 400, 'message': 'gpa 必须是数字'}), 400
                    # 可选：限制 GPA 合理范围
                    if gpa < 0 or gpa > 5:
                        return jsonify({'code': 400, 'message': 'gpa 必须在 0~5 之间'}), 400
                    student.gpa = gpa

            if 'birthplace' in base_info:
                bp = (base_info['birthplace'] or '').strip()
                student.birthplace = bp or None

            if 'phone' in base_info:
                phone = (base_info['phone'] or '').strip()
                # 如需更严格的校验可在此补充
                student.phone = phone or None

            if 'ethnicity' in base_info:
                ethnicity = (base_info['ethnicity'] or '').strip()
                student.ethnicity = ethnicity or None

            if 'political_affiliation' in base_info:
                political_affiliation = (base_info['political_affiliation'] or '').strip()
                student.political_affiliation = political_affiliation or None
        
        # 2. 更新四阶段状态（直接更新到 User 表的字段）
        process_status = data.get('process_status', {})
        if process_status:
            # 验证并更新各阶段状态
            for stage_name, status_value in process_status.items():
                if stage_name not in VALID_STAGES:
                    return jsonify({
                        'code': 400,
                        'message': f'无效的阶段名称: {stage_name}，支持的值: {", ".join(VALID_STAGES)}'
                    }), 400
                
                if status_value not in VALID_STATUSES:
                    return jsonify({
                        'code': 400,
                        'message': f'无效的状态值: {status_value}，支持的值: {", ".join(VALID_STATUSES)}'
                    }), 400
                
                # 更新阶段状态
                if stage_name == 'preliminary':
                    student.preliminary_status = status_value
                elif stage_name == 'medical':
                    student.medical_status = status_value
                elif stage_name == 'political':
                    student.political_status = status_value
                elif stage_name == 'admission':
                    student.admission_status = status_value
        
        # 3. 添加新评语（如果提供了 new_comment）
        new_comment = data.get('new_comment', '').strip()
        if new_comment:
            comment = Comment(
                user_id=student_id,
                content=new_comment,
                author=admin.name  # 使用管理员姓名作为作者
            )
            db.session.add(comment)
        
        # 提交事务（所有操作一起提交，确保原子性）
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '档案更新成功'
        }), 200
        
    except Exception as e:
        # 发生异常时回滚事务
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'档案更新失败: {str(e)}'
        }), 500


@admin_bp.route('/students/import', methods=['POST'])
@admin_required
def import_students_from_excel():
    """
    从 Excel 文件批量导入学生（管理员权限）
    
    请求格式: multipart/form-data
    字段名: 
    - file (Excel 文件)
    - department_id (部门ID，整数，必填)
    
    Excel 文件格式要求：
    - 第一行为列名：学号、姓名、身份证号
    - 支持 .xlsx 和 .xls 格式
    - 不需要包含班级名称，班级由前端传入的 department_id 指定
    
    逻辑：
    - 如果学号在数据库中已存在，则跳过该行
    - 如果身份证号已存在，则跳过该行
    - 所有学生将导入到指定的 department_id
    - 普通管理员只能导入到其管理的部门
    
    返回: {
        "code": 200,
        "data": {
            "success_count": 10,
            "skip_count": 2,
            "error_count": 1,
            "errors": [
                {"row": 3, "student_id": "2023001", "error": "学号已存在"},
                {"row": 5, "class_name": "不存在的班级", "error": "班级不存在"}
            ]
        },
        "message": "import completed"
    }
    
    依赖项：
    - pandas: pip install pandas
    - openpyxl: pip install openpyxl (用于读取 .xlsx 文件)
    """
    if not PANDAS_AVAILABLE:
        return jsonify({
            'code': 500,
            'message': 'pandas 未安装，请运行: pip install pandas openpyxl'
        }), 500
    
    admin_id = get_jwt_identity()
    admin = AdminUser.query.get(admin_id)
    
    if not admin:
        return jsonify({'code': 404, 'message': '管理员不存在'}), 404
    
    # 检查文件是否上传
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '未上传文件，请使用字段名 "file"'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'code': 400, 'message': '文件名为空'}), 400
    
    # 检查文件扩展名
    filename = file.filename.lower()
    if not (filename.endswith('.xlsx') or filename.endswith('.xls')):
        return jsonify({'code': 400, 'message': '不支持的文件格式，仅支持 .xlsx 和 .xls 文件'}), 400
    
    # 获取 department_id 参数
    department_id_str = request.form.get('department_id')
    if not department_id_str:
        return jsonify({'code': 400, 'message': '缺少必需参数: department_id'}), 400
    
    try:
        department_id = int(department_id_str)
    except (ValueError, TypeError):
        return jsonify({'code': 400, 'message': 'department_id 必须是整数'}), 400
    
    # 验证部门是否存在
    department = Department.query.get(department_id)
    if not department:
        return jsonify({'code': 404, 'message': f'部门ID {department_id} 不存在'}), 404
    
    # 获取管理员管理的部门列表（用于权限检查）
    if admin.role == AdminUser.ROLE_SUPER:
        managed_dept_ids = None  # 超级管理员可以访问所有部门
    else:
        managed_departments = admin.managed_departments.all()
        managed_dept_ids = [dept.id for dept in managed_departments]
        if not managed_dept_ids:
            return jsonify({'code': 403, 'message': '您没有管理的部门，无法导入学生'}), 403
        
        # 权限检查：普通管理员只能导入到其管理的部门
        if department_id not in managed_dept_ids:
            return jsonify({'code': 403, 'message': f'无权将学生导入到部门ID {department_id}'}), 403
    
    # 读取 Excel 文件
    try:
        # 使用 pandas 读取 Excel
        df = pd.read_excel(file, engine='openpyxl' if filename.endswith('.xlsx') else None)
    except Exception as e:
        return jsonify({
            'code': 400,
            'message': f'Excel 文件读取失败: {str(e)}'
        }), 400
    
    # 检查必需的列（不再需要班级名称列）
    required_columns = ['学号', '姓名', '身份证号']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        return jsonify({
            'code': 400,
            'message': f'Excel 文件缺少必需的列: {", ".join(missing_columns)}'
        }), 400
    
    # 统计数据
    success_count = 0
    skip_count = 0
    error_count = 0
    errors = []
    
    # 批量查询已存在的学号和身份证号（优化性能）
    existing_student_ids_query = User.query.with_entities(User.student_id).filter(
        User.student_id.isnot(None),
        User.student_id != ''
    ).all()
    existing_student_ids = {str(sid[0]) for sid in existing_student_ids_query if sid[0] and str(sid[0]).strip()}
    
    existing_id_cards_query = User.query.with_entities(User.id_card_no).all()
    existing_id_cards = {str(card[0]) for card in existing_id_cards_query if card[0]}
    
    # 准备批量插入的数据
    users_to_add = []
    
    # 遍历每一行数据
    for index, row in df.iterrows():
        row_num = index + 2  # Excel 行号（从2开始，因为第1行是列名）
        
        try:
            # 提取数据（去除前后空格）
            student_id = str(row['学号']).strip() if pd.notna(row['学号']) else ''
            name = str(row['姓名']).strip() if pd.notna(row['姓名']) else ''
            id_card_no = str(row['身份证号']).strip() if pd.notna(row['身份证号']) else ''
            
            # 基本验证
            if not name:
                errors.append({
                    'row': row_num,
                    'student_id': student_id,
                    'error': '姓名为空'
                })
                error_count += 1
                continue
            
            if not id_card_no:
                errors.append({
                    'row': row_num,
                    'student_id': student_id,
                    'error': '身份证号为空'
                })
                error_count += 1
                continue
            
            # 身份证号格式验证
            id_card_no = id_card_no.upper()  # 统一转为大写
            if len(id_card_no) != 18:
                errors.append({
                    'row': row_num,
                    'student_id': student_id,
                    'id_card_no': id_card_no,
                    'error': '身份证号必须为18位'
                })
                error_count += 1
                continue
            
            if (not id_card_no[:17].isdigit()) or (not (id_card_no[17].isdigit() or id_card_no[17] == 'X')):
                errors.append({
                    'row': row_num,
                    'student_id': student_id,
                    'id_card_no': id_card_no,
                    'error': '身份证号格式不正确'
                })
                error_count += 1
                continue
            
            # 检查身份证号是否已存在
            if id_card_no in existing_id_cards:
                skip_count += 1
                continue
            
            # 检查学号是否已存在（如果提供了学号）
            if student_id and student_id in existing_student_ids:
                skip_count += 1
                continue
            
            # 使用前端传入的 department_id（已在前面验证过）
            
            # 学号格式验证（如果提供了学号）
            if student_id:
                if not student_id.isdigit():
                    errors.append({
                        'row': row_num,
                        'student_id': student_id,
                        'error': '学号必须为纯数字'
                    })
                    error_count += 1
                    continue
            
            # 准备创建用户对象（使用前端传入的 department_id）
            # 使用部门的基础分，如果部门不存在则使用默认值80
            department_base_score = 80
            if department:
                department_base_score = department.base_score
            
            user = User(
                id_card_no=id_card_no,
                student_id=student_id if student_id else None,
                name=name,
                department_id=department_id,  # 使用前端传入的部门ID
                base_score=department_base_score  # 使用部门的基础分
            )
            # 设置默认密码（使用身份证号后6位作为初始密码）
            default_password = id_card_no[-6:]
            user.set_password(default_password)
            
            users_to_add.append(user)
            
            # 更新已存在的集合（避免同一批数据中的重复）
            if student_id:
                existing_student_ids.add(student_id)
            existing_id_cards.add(id_card_no)
            
        except Exception as e:
            errors.append({
                'row': row_num,
                'error': f'处理失败: {str(e)}'
            })
            error_count += 1
            continue
    
    # 批量插入数据库
    if users_to_add:
        try:
            db.session.add_all(users_to_add)
            db.session.commit()
            success_count = len(users_to_add)
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'code': 500,
                'message': f'批量导入失败: {str(e)}'
            }), 500
    
    return jsonify({
        'code': 200,
        'data': {
            'success_count': success_count,
            'skip_count': skip_count,
            'error_count': error_count,
            'errors': errors[:100]  # 最多返回100条错误信息，避免响应过大
        },
        'message': 'import completed'
    }), 200