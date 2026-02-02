"""add certificate dynamic form fields

为证书模块添加动态表单支持：
- certificate_types 表添加 form_schema 字段（JSON类型），用于存储表单定义
- certificates 表添加 extra_data 字段（JSON类型），用于存储动态表单填写的具体数据

Revision ID: 20260131_add_certificate_dynamic_form_fields
Revises: 20260130_add_department_base_score
Create Date: 2026-01-31
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260131_add_certificate_dynamic_form_fields'
down_revision = '20260130_add_department_base_score'
branch_labels = None
depends_on = None


def upgrade():
    # 为 certificate_types 表添加 form_schema 字段
    with op.batch_alter_table('certificate_types', schema=None) as batch_op:
        batch_op.add_column(sa.Column('form_schema', sa.JSON(), nullable=True, comment='表单定义（JSON格式），用于动态渲染输入框'))
    
    # 为 certificates 表添加 extra_data 字段
    with op.batch_alter_table('certificates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('extra_data', sa.JSON(), nullable=True, comment='额外数据（JSON格式），存储动态表单填写的具体数据'))


def downgrade():
    # 移除 extra_data 字段
    with op.batch_alter_table('certificates', schema=None) as batch_op:
        batch_op.drop_column('extra_data')
    
    # 移除 form_schema 字段
    with op.batch_alter_table('certificate_types', schema=None) as batch_op:
        batch_op.drop_column('form_schema')

