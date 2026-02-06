"""add user ethnicity field

在 users 表添加民族字段：
- ethnicity: 民族

Revision ID: 20260202_add_user_ethnicity_field
Revises: 20260201_add_user_info_fields
Create Date: 2026-02-02
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260202_add_user_ethnicity_field'
down_revision = '20260201_add_user_info_fields'
branch_labels = None
depends_on = None


def upgrade():
    # 添加民族字段到 users 表
    op.add_column('users', sa.Column('ethnicity', sa.String(length=50), nullable=True, comment='民族'))


def downgrade():
    # 删除民族字段
    op.drop_column('users', 'ethnicity')


