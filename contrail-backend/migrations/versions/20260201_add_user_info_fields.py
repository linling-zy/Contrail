"""add user info fields

在 users 表添加学生信息补充字段：
- credits: 学分
- gpa: 绩点
- birthplace: 籍贯
- phone: 联系电话

Revision ID: 20260201_add_user_info_fields
Revises: merge_branches
Create Date: 2026-02-01
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260201_add_user_info_fields'
down_revision = 'merge_branches'
branch_labels = None
depends_on = None


def upgrade():
    # 添加学生信息补充字段到 users 表
    op.add_column('users', sa.Column('credits', sa.Float(), nullable=True, comment='学分'))
    op.add_column('users', sa.Column('gpa', sa.Float(), nullable=True, comment='绩点'))
    op.add_column('users', sa.Column('birthplace', sa.String(length=100), nullable=True, comment='籍贯'))
    op.add_column('users', sa.Column('phone', sa.String(length=20), nullable=True, comment='联系电话'))


def downgrade():
    # 删除学生信息补充字段
    op.drop_column('users', 'phone')
    op.drop_column('users', 'birthplace')
    op.drop_column('users', 'gpa')
    op.drop_column('users', 'credits')

