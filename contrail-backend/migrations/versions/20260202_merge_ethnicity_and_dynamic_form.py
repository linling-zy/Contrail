"""merge ethnicity and dynamic form branches

合并迁移分支：
- 20260131_add_certificate_dynamic_form_fields
- 20260202_add_user_ethnicity_field

Revision ID: 20260202_merge_ethnicity_and_dynamic_form
Revises: 20260131_add_certificate_dynamic_form_fields, 20260202_add_user_ethnicity_field
Create Date: 2026-02-02
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260202_merge_ethnicity_and_dynamic_form'
down_revision = ('20260131_add_certificate_dynamic_form_fields', '20260202_add_user_ethnicity_field')
branch_labels = None
depends_on = None


def upgrade():
    # 合并迁移不需要执行任何操作，因为两个分支的更改已经应用
    pass


def downgrade():
    # 合并迁移不需要执行任何操作
    pass


