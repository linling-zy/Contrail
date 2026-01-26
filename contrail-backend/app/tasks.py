"""
定时任务模块
实现每周和每月的自动加分逻辑
"""
from datetime import datetime, timedelta
from app.extensions import db, scheduler
from app.models import User, ScoreLog


def weekly_bonus():
    """
    每周奖励任务
    检查所有学生在过去7天内是否有扣分记录 (delta < 0)
    如果没有扣分，自动插入一条 +1 分的 ScoreLog
    """
    print(f"[定时任务] 开始执行每周奖励任务 - {datetime.now()}")
    
    # 计算7天前的时间点
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # 获取所有用户
    users = User.query.all()
    bonus_count = 0
    
    for user in users:
        # 检查该用户在过去7天内是否有扣分记录
        has_deduction = ScoreLog.query.filter(
            ScoreLog.user_id == user.id,
            ScoreLog.delta < 0,  # 扣分记录
            ScoreLog.create_time >= seven_days_ago
        ).first()
        
        # 如果没有扣分记录，给予奖励
        if not has_deduction:
            # 检查本周是否已经给过奖励（避免重复）
            this_week_bonus = ScoreLog.query.filter(
                ScoreLog.user_id == user.id,
                ScoreLog.delta == 1,
                ScoreLog.reason == '每周全勤奖励',
                ScoreLog.type == ScoreLog.TYPE_SYSTEM,
                ScoreLog.create_time >= seven_days_ago
            ).first()
            
            if not this_week_bonus:
                # 创建奖励记录
                score_log = ScoreLog(
                    user_id=user.id,
                    delta=1,
                    reason='每周全勤奖励',
                    type=ScoreLog.TYPE_SYSTEM
                )
                db.session.add(score_log)
                bonus_count += 1
                user_key = getattr(user, 'id_card_no', None) or getattr(user, 'student_id', None) or str(user.id)
                print(f"  ✓ 用户 {user_key} ({user.name}) 获得每周奖励 +1分")
    
    db.session.commit()
    print(f"[定时任务] 每周奖励任务完成，共奖励 {bonus_count} 位学生")
    return bonus_count


def monthly_bonus():
    """
    每月奖励任务
    检查所有学生在过去30天内是否有扣分记录 (delta < 0)
    如果没有扣分，自动插入一条 +2 分的 ScoreLog
    """
    print(f"[定时任务] 开始执行每月奖励任务 - {datetime.now()}")
    
    # 计算30天前的时间点
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # 获取所有用户
    users = User.query.all()
    bonus_count = 0
    
    for user in users:
        # 检查该用户在过去30天内是否有扣分记录
        has_deduction = ScoreLog.query.filter(
            ScoreLog.user_id == user.id,
            ScoreLog.delta < 0,  # 扣分记录
            ScoreLog.create_time >= thirty_days_ago
        ).first()
        
        # 如果没有扣分记录，给予奖励
        if not has_deduction:
            # 检查本月是否已经给过奖励（避免重复）
            this_month_bonus = ScoreLog.query.filter(
                ScoreLog.user_id == user.id,
                ScoreLog.delta == 2,
                ScoreLog.reason == '每月全勤奖励',
                ScoreLog.type == ScoreLog.TYPE_SYSTEM,
                ScoreLog.create_time >= thirty_days_ago
            ).first()
            
            if not this_month_bonus:
                # 创建奖励记录
                score_log = ScoreLog(
                    user_id=user.id,
                    delta=2,
                    reason='每月全勤奖励',
                    type=ScoreLog.TYPE_SYSTEM
                )
                db.session.add(score_log)
                bonus_count += 1
                user_key = getattr(user, 'id_card_no', None) or getattr(user, 'student_id', None) or str(user.id)
                print(f"  ✓ 用户 {user_key} ({user.name}) 获得每月奖励 +2分")
    
    db.session.commit()
    print(f"[定时任务] 每月奖励任务完成，共奖励 {bonus_count} 位学生")
    return bonus_count


def register_scheduled_tasks():
    """
    注册定时任务到调度器
    在应用初始化时调用
    """
    # 每周一凌晨 2:00 执行每周奖励任务
    scheduler.add_job(
        id='weekly_bonus',
        func=weekly_bonus,
        trigger='cron',
        day_of_week='mon',  # 周一
        hour=2,  # 凌晨2点
        minute=0,
        replace_existing=True
    )
    
    # 每月1号凌晨 3:00 执行每月奖励任务
    scheduler.add_job(
        id='monthly_bonus',
        func=monthly_bonus,
        trigger='cron',
        day=1,  # 每月1号
        hour=3,  # 凌晨3点
        minute=0,
        replace_existing=True
    )
    
    print("[定时任务] 已注册定时任务：")
    print("  - 每周奖励任务：每周一 02:00")
    print("  - 每月奖励任务：每月1号 03:00")

