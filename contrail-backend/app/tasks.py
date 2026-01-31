"""
定时任务模块
实现每周和每月的自动加分逻辑（按部门管理考核时间）
"""
import logging
from datetime import datetime, timedelta, date
from app.extensions import db, scheduler
from app.models import User, ScoreLog, Department, SystemConfig


logger = logging.getLogger(__name__)


def _get_default_bonus_start_date():
    """
    获取全局默认的自动加分起始日期
    
    Returns:
        date: 默认起始日期（默认为 '2024-01-01'）
    """
    default_date_str = SystemConfig.get_config('bonus_start_date', '2024-01-01')
    try:
        return datetime.strptime(default_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        # 如果配置格式错误，返回默认日期
        return date(2024, 1, 1)


def _process_bonus(users, days_back, bonus_delta, bonus_reason):
    """
    处理奖励逻辑（检查指定天数内是否有扣分，无扣分则奖励）
    
    Args:
        users: 用户查询对象或用户列表
        days_back: 检查过去多少天（7天或30天）
        bonus_delta: 奖励分数（1分或2分）
        bonus_reason: 奖励原因说明
    
    Returns:
        int: 奖励的学生数量
    """
    if not users:
        return 0
    
    # 如果传入的是查询对象，转换为列表
    if hasattr(users, 'all'):
        users = users.all()
    
    bonus_count = 0
    check_start_time = datetime.utcnow() - timedelta(days=days_back)
    
    for user in users:
        # 检查该用户在过去指定天数内是否有扣分记录
        has_deduction = ScoreLog.query.filter(
            ScoreLog.user_id == user.id,
            ScoreLog.delta < 0,  # 扣分记录
            ScoreLog.create_time >= check_start_time
        ).first()
        
        # 如果没有扣分记录，给予奖励
        if not has_deduction:
            # 检查是否已经给过奖励（避免重复）
            existing_bonus = ScoreLog.query.filter(
                ScoreLog.user_id == user.id,
                ScoreLog.delta == bonus_delta,
                ScoreLog.reason == bonus_reason,
                ScoreLog.type == ScoreLog.TYPE_SYSTEM,
                ScoreLog.create_time >= check_start_time
            ).first()
            
            if not existing_bonus:
                # 创建奖励记录
                score_log = ScoreLog(
                    user_id=user.id,
                    delta=bonus_delta,
                    reason=bonus_reason,
                    type=ScoreLog.TYPE_SYSTEM
                )
                db.session.add(score_log)
                bonus_count += 1
                user_key = getattr(user, 'id_card_no', None) or getattr(user, 'student_id', None) or str(user.id)
                logger.info(f"  ✓ 用户 {user_key} ({user.name}) 获得{bonus_reason} +{bonus_delta}分")
    
    return bonus_count


def check_and_award_bonus():
    """
    统一的自动加分检查函数（按部门轮询模式）
    遍历所有部门，根据每个部门的考核起始日期判断是否触发周/月奖励
    """
    logger.info(f"[定时任务] 开始执行自动加分检查任务 - {datetime.now()}")
    
    # 1. 获取全局默认起始日期
    default_start_date = _get_default_bonus_start_date()
    logger.info(f"[定时任务] 全局默认起始日期: {default_start_date}")
    
    # 2. 获取今天日期
    today = date.today()
    
    # 3. 查询所有部门
    departments = Department.query.all()
    logger.info(f"[定时任务] 共找到 {len(departments)} 个部门")
    
    total_weekly_bonus = 0
    total_monthly_bonus = 0
    
    # 4. 遍历每个部门
    for dept in departments:
        # 确定该部门的起始日期（优先取部门配置，若为空则取全局默认）
        dept_start_date = dept.bonus_start_date if dept.bonus_start_date else default_start_date
        
        # 计算天数差
        days_diff = (today - dept_start_date).days
        
        # 如果起始日期在未来，跳过该部门
        if days_diff <= 0:
            dept_name = f"{dept.college}/{dept.grade}/{dept.major}/{dept.class_name}" or f"部门#{dept.id}"
            logger.info(f"  [部门 {dept_name}] 起始日期 {dept_start_date} 尚未到达，跳过")
            continue
        
        # 判断是否触发周奖励（每7天）
        is_weekly = (days_diff % 7 == 0)
        # 判断是否触发月奖励（每30天）
        is_monthly = (days_diff % 30 == 0)
        
        dept_name = f"{dept.college}/{dept.grade}/{dept.major}/{dept.class_name}" or f"部门#{dept.id}"
        
        if is_weekly or is_monthly:
            logger.info(f"  [部门 {dept_name}] 起始日期: {dept_start_date}, 天数差: {days_diff}天")
            
            # 获取该部门下的所有学生
            dept_users = dept.users
            
            if is_weekly:
                logger.info("    → 触发周奖励检查（7天无扣分）")
                weekly_count = _process_bonus(
                    dept_users,
                    days_back=7,
                    bonus_delta=1,
                    bonus_reason='每周全勤奖励'
                )
                total_weekly_bonus += weekly_count
                logger.info(f"    → 部门 {dept_name} 周奖励: {weekly_count} 位学生")
            
            if is_monthly:
                logger.info("    → 触发月奖励检查（30天无扣分）")
                monthly_count = _process_bonus(
                    dept_users,
                    days_back=30,
                    bonus_delta=2,
                    bonus_reason='每月全勤奖励'
                )
                total_monthly_bonus += monthly_count
                logger.info(f"    → 部门 {dept_name} 月奖励: {monthly_count} 位学生")
    
    # 提交所有更改
    db.session.commit()
    
    logger.info("[定时任务] 自动加分检查完成")
    logger.info(f"  - 周奖励: {total_weekly_bonus} 位学生")
    logger.info(f"  - 月奖励: {total_monthly_bonus} 位学生")
    
    return {
        'weekly_bonus': total_weekly_bonus,
        'monthly_bonus': total_monthly_bonus
    }


def register_scheduled_tasks():
    """
    注册定时任务到调度器
    在应用初始化时调用
    
    注意：仅保留每日执行一次的统一检查任务，避免周/月任务重复触发导致冗余加分。
    新的 check_and_award_bonus 函数已经通过计算日期差涵盖了所有的奖励逻辑。
    """
    # 每天凌晨 1:00 执行一次统一的检查函数
    scheduler.add_job(
        id='daily_bonus_check',
        func=check_and_award_bonus,
        trigger='cron',
        hour=1,  # 凌晨1点
        minute=0,
        replace_existing=True
    )
    
    logger.info("[定时任务] 已注册定时任务：")
    logger.info("  - 每日检查任务：每天 01:00（统一按部门检查周/月奖励）")
