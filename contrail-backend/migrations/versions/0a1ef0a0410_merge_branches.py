"""merge branches

合并迁移分支：
- 20260130_add_department_base_score
- 20260131_add_certificate_extra_data

Revision ID: 0a1ef0a0410
Revises: 20260130_add_department_base_score, 20260131_add_certificate_extra_data
Create Date: 2026-01-31 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_branches'
down_revision = ('20260130_add_department_base_score', '20260131_add_certificate_extra_data')
branch_labels = None
depends_on = None


def upgrade():
    # 合并迁移不需要执行任何操作，因为两个分支的更改已经应用
    pass


def downgrade():
    # 合并迁移不需要执行任何操作
    pass

