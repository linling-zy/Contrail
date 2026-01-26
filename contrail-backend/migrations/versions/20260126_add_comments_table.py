"""add comments table

创建 comments 表用于存储学生评语信息，支持历史记录：
- user_id: 外键关联 users.id
- content: 评语内容（Text 类型，支持长文本）
- author: 评语作者（可选，管理员姓名或系统标识）
- create_time: 创建时间
- update_time: 更新时间

Revision ID: 20260126_add_comments
Revises: 20260126_add_process_status
Create Date: 2026-01-26
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260126_add_comments"
down_revision = "20260126_add_process_status"
branch_labels = None
depends_on = None


def upgrade():
    # 创建 comments 表
    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, comment="评语ID，主键"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="用户内部ID（外键关联）"),
        sa.Column("content", sa.Text(), nullable=False, comment="评语内容"),
        sa.Column("author", sa.String(length=50), nullable=True, comment="评语作者（管理员姓名或系统标识）"),
        sa.Column("create_time", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("update_time", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_comments_user_id_users"),
    )
    op.create_index("ix_comments_user_id", "comments", ["user_id"])
    op.create_index("ix_comments_create_time", "comments", ["create_time"])


def downgrade():
    # 删除 comments 表
    try:
        op.drop_index("ix_comments_create_time", table_name="comments")
        op.drop_index("ix_comments_user_id", table_name="comments")
    except Exception:
        pass
    op.drop_table("comments")

