"""add process status fields to users

在 users 表添加录取流程四阶段状态字段：
- preliminary_status: 初试状态
- medical_status: 体检状态
- political_status: 政审状态
- admission_status: 录取状态

每个字段默认值为 'pending'，可选值：qualified/pending/unqualified

Revision ID: 20260126_add_process_status
Revises: 20260124_initial_schema
Create Date: 2026-01-26
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260126_add_process_status"
down_revision = "20260124_initial_schema"
branch_labels = None
depends_on = None


def upgrade():
    # 添加四阶段状态字段到 users 表
    op.add_column('users', sa.Column('preliminary_status', sa.String(length=20), nullable=False, server_default='pending', comment='初试状态：qualified/pending/unqualified'))
    op.add_column('users', sa.Column('medical_status', sa.String(length=20), nullable=False, server_default='pending', comment='体检状态：qualified/pending/unqualified'))
    op.add_column('users', sa.Column('political_status', sa.String(length=20), nullable=False, server_default='pending', comment='政审状态：qualified/pending/unqualified'))
    op.add_column('users', sa.Column('admission_status', sa.String(length=20), nullable=False, server_default='pending', comment='录取状态：qualified/pending/unqualified'))


def downgrade():
    # 删除四阶段状态字段
    op.drop_column('users', 'admission_status')
    op.drop_column('users', 'political_status')
    op.drop_column('users', 'medical_status')
    op.drop_column('users', 'preliminary_status')

