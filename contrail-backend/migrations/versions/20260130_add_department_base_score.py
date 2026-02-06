"""add department base_score

为 departments 表添加 base_score 字段，用于定义部门成员的基础分

Revision ID: 20260130_add_department_base_score
Revises: 3123f97a8e6e
Create Date: 2026-01-30
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260130_add_department_base_score'
down_revision = '3123f97a8e6e'
branch_labels = None
depends_on = None


def upgrade():
    # 为 departments 表添加 base_score 字段
    with op.batch_alter_table('departments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('base_score', sa.Integer(), nullable=False, server_default='80', comment='部门成员的基础分，默认80分'))


def downgrade():
    # 移除 base_score 字段
    with op.batch_alter_table('departments', schema=None) as batch_op:
        batch_op.drop_column('base_score')




