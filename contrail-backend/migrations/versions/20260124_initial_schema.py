"""initial schema (squashed)

从空数据库直接创建当前最新表结构：
- departments
- users (id_card_no 登录账号；student_id 可空补充字段；department_id 外键)
- score_logs
- certificates

Revision ID: 20260124_initial_schema
Revises:
Create Date: 2026-01-24
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260124_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # departments
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, comment="部门ID，主键"),
        sa.Column("college", sa.String(length=100), nullable=True, comment="学院"),
        sa.Column("grade", sa.String(length=20), nullable=True, comment="年级"),
        sa.Column("major", sa.String(length=100), nullable=True, comment="专业"),
        sa.Column("class_name", sa.String(length=50), nullable=True, comment="班级"),
        sa.Column("create_time", sa.DateTime(), nullable=True, comment="创建时间"),
    )
    op.create_index("ix_departments_college", "departments", ["college"])
    op.create_index("ix_departments_grade", "departments", ["grade"])
    op.create_index("ix_departments_major", "departments", ["major"])
    op.create_index("ix_departments_class_name", "departments", ["class_name"])

    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, comment="内部用户ID，主键"),
        sa.Column("id_card_no", sa.String(length=18), nullable=False, comment="身份证号，业务唯一标识/登录账号"),
        sa.Column("student_id", sa.String(length=20), nullable=True, comment="学号（可选），业务补充字段"),
        sa.Column("name", sa.String(length=50), nullable=False, comment="姓名"),
        sa.Column("password_hash", sa.String(length=255), nullable=False, comment="密码哈希值"),
        sa.Column("base_score", sa.Integer(), nullable=False, server_default="80", comment="基础分，默认80分"),
        sa.Column("department_id", sa.Integer(), nullable=True, comment="部门ID（外键关联 departments.id）"),
        sa.Column("create_time", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("update_time", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], name="fk_users_department_id_departments"),
    )
    op.create_index("ix_users_id_card_no", "users", ["id_card_no"], unique=True)
    op.create_index("ix_users_student_id", "users", ["student_id"], unique=True)
    op.create_index("ix_users_department_id", "users", ["department_id"])

    # score_logs
    op.create_table(
        "score_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="用户内部ID（外键关联）"),
        sa.Column("delta", sa.Integer(), nullable=False, comment="变动分数，正数为加分，负数为扣分"),
        sa.Column("reason", sa.String(length=200), nullable=True, comment="变动原因说明"),
        sa.Column("type", sa.String(length=20), nullable=False, server_default="manual", comment="变动类型：system(系统) 或 manual(人工)"),
        sa.Column("create_time", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_score_logs_user_id_users"),
    )
    op.create_index("ix_score_logs_user_id", "score_logs", ["user_id"])
    op.create_index("ix_score_logs_create_time", "score_logs", ["create_time"])

    # certificates
    op.create_table(
        "certificates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="用户内部ID（外键关联）"),
        sa.Column("name", sa.String(length=100), nullable=False, comment="证书名称"),
        sa.Column("image_url", sa.String(length=500), nullable=False, comment="证书图片URL"),
        sa.Column("status", sa.Integer(), nullable=False, server_default="0", comment="审核状态：0待审/1通过/2驳回"),
        sa.Column("reject_reason", sa.String(length=200), nullable=True, comment="驳回原因（仅当status=2时有效）"),
        sa.Column("upload_time", sa.DateTime(), nullable=False, comment="上传时间"),
        sa.Column("review_time", sa.DateTime(), nullable=True, comment="审核时间"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_certificates_user_id_users"),
    )
    op.create_index("ix_certificates_user_id", "certificates", ["user_id"])
    op.create_index("ix_certificates_status", "certificates", ["status"])


def downgrade():
    # 按依赖顺序删除
    try:
        op.drop_index("ix_certificates_status", table_name="certificates")
        op.drop_index("ix_certificates_user_id", table_name="certificates")
    except Exception:
        pass
    op.drop_table("certificates")

    try:
        op.drop_index("ix_score_logs_create_time", table_name="score_logs")
        op.drop_index("ix_score_logs_user_id", table_name="score_logs")
    except Exception:
        pass
    op.drop_table("score_logs")

    try:
        op.drop_index("ix_users_department_id", table_name="users")
        op.drop_index("ix_users_student_id", table_name="users")
        op.drop_index("ix_users_id_card_no", table_name="users")
    except Exception:
        pass
    op.drop_table("users")

    try:
        op.drop_index("ix_departments_class_name", table_name="departments")
        op.drop_index("ix_departments_major", table_name="departments")
        op.drop_index("ix_departments_grade", table_name="departments")
        op.drop_index("ix_departments_college", table_name="departments")
    except Exception:
        pass
    op.drop_table("departments")



