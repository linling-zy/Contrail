"""add user political affiliation field

在 users 表添加政治面貌字段：
- political_affiliation: 政治面貌（如：中共党员、共青团员、群众等）

Revision ID: 20260203_add_user_political_affiliation_field
Revises: 20260202_merge_ethnicity_and_dynamic_form
Create Date: 2026-02-03
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260203_add_user_political_affiliation_field'
down_revision = '20260202_merge_ethnicity_and_dynamic_form'
branch_labels = None
depends_on = None


def upgrade():
    # 添加政治面貌字段到 users 表
    op.add_column('users', sa.Column('political_affiliation', sa.String(length=50), nullable=True, comment='政治面貌（如：中共党员、共青团员、群众等）'))


def downgrade():
    # 删除政治面貌字段
    op.drop_column('users', 'political_affiliation')


