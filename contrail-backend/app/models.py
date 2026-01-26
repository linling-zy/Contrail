"""
数据库模型定义
包含 User, ScoreLog, Certificate, Comment, CertificateType 五个核心模型
"""
from datetime import datetime
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


class Department(db.Model):
    """
    部门/组织模型

    用于承载原先挂在 User 上的学院/年级/专业/班级信息，用户通过 department_id 绑定到一个部门。
    """

    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='部门ID，主键')
    college = db.Column(db.String(100), nullable=True, index=True, comment='学院')
    grade = db.Column(db.String(20), nullable=True, index=True, comment='年级')
    major = db.Column(db.String(100), nullable=True, index=True, comment='专业')
    class_name = db.Column(db.String(50), nullable=True, index=True, comment='班级')
    create_time = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')

    # 关系：一个部门有多个用户
    users = db.relationship('User', backref='department', lazy='dynamic')
    
    # 关系：一个部门需要多种证书类型（多对多）
    certificate_types = db.relationship(
        'CertificateType',
        secondary='department_certificate_types',
        backref='departments',
        lazy='dynamic'
    )

    def to_dict(self):
        return {
            'id': self.id,
            'college': self.college,
            'grade': self.grade,
            'major': self.major,
            'class_name': self.class_name,
        }

    def __repr__(self):
        return f'<Department {self.id} {self.college}/{self.grade}/{self.major}/{self.class_name}>'


class User(db.Model):
    """
    用户模型
    存储学生基本信息
    使用内部自增 id 作为主键，id_card_no(身份证号) 用于登录/业务唯一标识；student_id(学号) 为可选补充字段
    """
    __tablename__ = 'users'
    
    # 内部主键 ID（自增，用于数据库关联和 JWT 认证）
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='内部用户ID，主键')
    # 身份证号（用于登录，业务唯一标识）
    id_card_no = db.Column(db.String(18), unique=True, nullable=False, index=True, comment='身份证号，业务唯一标识/登录账号')
    # 学号（可选补充字段，允许为空；如果填写则应唯一）
    student_id = db.Column(db.String(20), unique=True, nullable=True, index=True, comment='学号（可选），业务补充字段')
    name = db.Column(db.String(50), nullable=False, comment='姓名')
    password_hash = db.Column(db.String(255), nullable=False, comment='密码哈希值')
    base_score = db.Column(db.Integer, default=80, nullable=False, comment='基础分，默认80分')

    # 用户绑定部门（可为空，兼容未完善信息的用户）
    department_id = db.Column(
        db.Integer,
        db.ForeignKey('departments.id'),
        nullable=True,
        index=True,
        comment='部门ID（外键关联 departments.id）'
    )
    create_time = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 录取流程四阶段状态（qualified: 通过, pending: 待处理, unqualified: 未通过）
    preliminary_status = db.Column(db.String(20), default='pending', nullable=False, comment='初试状态：qualified/pending/unqualified')
    medical_status = db.Column(db.String(20), default='pending', nullable=False, comment='体检状态：qualified/pending/unqualified')
    political_status = db.Column(db.String(20), default='pending', nullable=False, comment='政审状态：qualified/pending/unqualified')
    admission_status = db.Column(db.String(20), default='pending', nullable=False, comment='录取状态：qualified/pending/unqualified')
    
    # 关系：一个用户有多条积分流水记录
    score_logs = db.relationship('ScoreLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    # 关系：一个用户有多个证书
    certificates = db.relationship('Certificate', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    # 关系：一个用户有多条评语记录
    comments = db.relationship('Comment', backref='user', lazy='dynamic', cascade='all, delete-orphan', order_by='Comment.create_time.desc()')
    
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
        # 为了尽量减少前端改动：仍返回 college/grade/major/class_name，但数据来自 department
        dept = getattr(self, 'department', None)
        data = {
            'id': self.id,  # 内部 ID（主键）
            'id_card_no': self.id_card_no,  # 身份证号（登录/业务标识）
            'student_id': self.student_id,  # 学号（可选补充字段）
            'name': self.name,
            'base_score': self.base_score,
            'department_id': self.department_id,
            'department': dept.to_dict() if dept else None,
            'college': dept.college if dept else None,
            'grade': dept.grade if dept else None,
            'major': dept.major if dept else None,
            'class_name': dept.class_name if dept else None,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'preliminary_status': self.preliminary_status,
            'medical_status': self.medical_status,
            'political_status': self.political_status,
            'admission_status': self.admission_status,
        }
        if include_score:
            data['total_score'] = self.total_score
        return data
    
    def __repr__(self):
        return f'<User {self.id_card_no}: {self.name}>'


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
    # 外键关联到 users.id（内部 ID，不是学号）
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True, comment='用户内部ID（外键关联）')
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
    # 外键关联到 users.id（内部 ID，不是学号）
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True, comment='用户内部ID（外键关联）')
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


class Comment(db.Model):
    """
    评语模型
    存储学生的评语信息，支持历史记录（可记录多次评语的变更）
    """
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='评语ID，主键')
    # 外键关联到 users.id（内部 ID，不是学号）
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True, comment='用户内部ID（外键关联）')
    content = db.Column(db.Text, nullable=False, comment='评语内容')
    author = db.Column(db.String(50), nullable=True, comment='评语作者（管理员姓名或系统标识）')
    create_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True, comment='更新时间')
    
    def to_dict(self):
        """转换为字典（用于 JSON 序列化）"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content': self.content,
            'author': self.author,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None,
        }
    
    def __repr__(self):
        return f'<Comment {self.id}: user_id={self.user_id} (content={self.content[:20]}...)'


# 部门和证书类型的多对多关联表
department_certificate_types = db.Table(
    'department_certificate_types',
    db.Column('department_id', db.Integer, db.ForeignKey('departments.id'), primary_key=True, comment='部门ID'),
    db.Column('certificate_type_id', db.Integer, db.ForeignKey('certificate_types.id'), primary_key=True, comment='证书类型ID'),
    db.Column('create_time', db.DateTime, default=datetime.utcnow, comment='关联创建时间')
)


class CertificateType(db.Model):
    """
    证书类型模型
    存储证书类型/名称信息，与部门多对多关联（一个部门需要多种证书，一种证书可能被多个部门需要）
    """
    __tablename__ = 'certificate_types'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='证书类型ID，主键')
    name = db.Column(db.String(100), nullable=False, unique=True, index=True, comment='证书名称（如：英语四级、计算机二级）')
    description = db.Column(db.String(500), nullable=True, comment='证书描述（可选）')
    is_required = db.Column(db.Boolean, default=True, nullable=False, comment='是否必填（默认必填）')
    create_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True, comment='更新时间')
    
    def to_dict(self):
        """转换为字典（用于 JSON 序列化）"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_required': self.is_required,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None,
        }
    
    def __repr__(self):
        return f'<CertificateType {self.id}: {self.name}>'

