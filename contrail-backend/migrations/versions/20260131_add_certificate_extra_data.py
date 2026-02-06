"""add certificate extra_data field

为 certificates 表添加 extra_data 字段（JSON类型），用于存储证书的额外信息：
- 英语四级/六级：分数
- 雅思IELTS：听力、阅读、写作、口语、总分
- 任职情况：任职时间、职务、集体获奖情况
- 获奖情况：奖励时间、主办单位、奖励级别、获奖等次

Revision ID: 20260131_add_certificate_extra_data
Revises: 3123f97a8e6e
Create Date: 2026-01-31
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260131_add_certificate_extra_data'
down_revision = '3123f97a8e6e'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 extra_data 字段
    # 注意：SQLite 不支持原生 JSON 类型，会存储为 TEXT
    # MySQL 5.7+ 和 PostgreSQL 支持 JSON 类型
    # 这里使用 JSON 类型，SQLAlchemy 会根据数据库类型自动适配
    with op.batch_alter_table('certificates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('extra_data', sa.JSON(), nullable=True, comment='额外数据（JSON格式），用于存储分数、任职情况、获奖情况等详细信息'))


def downgrade():
    # 删除 extra_data 字段
    with op.batch_alter_table('certificates', schema=None) as batch_op:
        batch_op.drop_column('extra_data')


