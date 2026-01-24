"""
数据库模型定义
包含 User, ScoreLog, Certificate 三个核心模型
"""
from datetime import datetime
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    """
    用户模型
    存储学生基本信息
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False, index=True, comment='学号，唯一标识')
    name = db.Column(db.String(50), nullable=False, comment='姓名')
    password_hash = db.Column(db.String(255), nullable=False, comment='密码哈希值')
    base_score = db.Column(db.Integer, default=80, nullable=False, comment='基础分，默认80分')
    class_info = db.Column(db.String(100), nullable=True, comment='班级信息')
    create_time = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系：一个用户有多条积分流水记录
    score_logs = db.relationship('ScoreLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    # 关系：一个用户有多个证书
    certificates = db.relationship('Certificate', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """设置密码（自动哈希）"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def total_score(self):
        """
        计算用户动态总分
        总分 = 基础分 + 所有积分变动的总和
        """
        total_delta = db.session.query(db.func.sum(ScoreLog.delta)).filter_by(user_id=self.id).scalar() or 0
        return self.base_score + total_delta
    
    def to_dict(self, include_score=True):
        """转换为字典（用于 JSON 序列化）"""
        data = {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.name,
            'base_score': self.base_score,
            'class_info': self.class_info,
            'create_time': self.create_time.isoformat() if self.create_time else None,
        }
        if include_score:
            data['total_score'] = self.total_score
        return data
    
    def __repr__(self):
        return f'<User {self.student_id}: {self.name}>'


class ScoreLog(db.Model):
    """
    积分流水模型
    记录所有积分变动历史
    """
    __tablename__ = 'score_logs'
    
    # 积分变动类型枚举
    TYPE_SYSTEM = 'system'  # 系统自动奖励
    TYPE_MANUAL = 'manual'  # 人工操作
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True, comment='用户ID')
    delta = db.Column(db.Integer, nullable=False, comment='变动分数，正数为加分，负数为扣分')
    reason = db.Column(db.String(200), nullable=True, comment='变动原因说明')
    type = db.Column(db.String(20), default=TYPE_MANUAL, nullable=False, comment='变动类型：system(系统) 或 manual(人工)')
    create_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True, comment='创建时间')
    
    def to_dict(self):
        """转换为字典（用于 JSON 序列化）"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'delta': self.delta,
            'reason': self.reason,
            'type': self.type,
            'create_time': self.create_time.isoformat() if self.create_time else None,
        }
    
    def __repr__(self):
        return f'<ScoreLog user_id={self.user_id} delta={self.delta}>'


class Certificate(db.Model):
    """
    证书模型
    存储学生上传的证书信息及审核状态
    """
    __tablename__ = 'certificates'
    
    # 审核状态枚举
    STATUS_PENDING = 0  # 待审核
    STATUS_APPROVED = 1  # 通过
    STATUS_REJECTED = 2  # 驳回
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True, comment='用户ID')
    name = db.Column(db.String(100), nullable=False, comment='证书名称')
    image_url = db.Column(db.String(500), nullable=False, comment='证书图片URL')
    status = db.Column(db.Integer, default=STATUS_PENDING, nullable=False, index=True, comment='审核状态：0待审/1通过/2驳回')
    reject_reason = db.Column(db.String(200), nullable=True, comment='驳回原因（仅当status=2时有效）')
    upload_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, comment='上传时间')
    review_time = db.Column(db.DateTime, nullable=True, comment='审核时间')
    
    def to_dict(self):
        """转换为字典（用于 JSON 序列化）"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'image_url': self.image_url,
            'status': self.status,
            'status_text': self.get_status_text(),
            'reject_reason': self.reject_reason,
            'upload_time': self.upload_time.isoformat() if self.upload_time else None,
            'review_time': self.review_time.isoformat() if self.review_time else None,
        }
    
    def get_status_text(self):
        """获取状态文本"""
        status_map = {
            self.STATUS_PENDING: '待审核',
            self.STATUS_APPROVED: '通过',
            self.STATUS_REJECTED: '驳回'
        }
        return status_map.get(self.status, '未知')
    
    def __repr__(self):
        return f'<Certificate {self.id}: {self.name} (status={self.status})>'

