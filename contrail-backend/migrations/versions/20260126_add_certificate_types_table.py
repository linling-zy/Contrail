"""add certificate types table

创建证书类型表和部门-证书类型关联表：
- certificate_types: 证书类型表（存储证书名称、描述、是否必填等）
- department_certificate_types: 部门和证书类型的多对多关联表

Revision ID: 20260126_add_certificate_types
Revises: 20260126_add_comments
Create Date: 2026-01-26
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260126_add_certificate_types"
down_revision = "20260126_add_comments"
branch_labels = None
depends_on = None


def upgrade():
    # 创建 certificate_types 表
    op.create_table(
        "certificate_types",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, comment="证书类型ID，主键"),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True, comment="证书名称（如：英语四级、计算机二级）"),
        sa.Column("description", sa.String(length=500), nullable=True, comment="证书描述（可选）"),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default="1", comment="是否必填（默认必填）"),
        sa.Column("create_time", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("update_time", sa.DateTime(), nullable=True, comment="更新时间"),
    )
    op.create_index("ix_certificate_types_name", "certificate_types", ["name"], unique=True)
    
    # 创建 department_certificate_types 关联表
    op.create_table(
        "department_certificate_types",
        sa.Column("department_id", sa.Integer(), nullable=False, comment="部门ID"),
        sa.Column("certificate_type_id", sa.Integer(), nullable=False, comment="证书类型ID"),
        sa.Column("create_time", sa.DateTime(), nullable=True, comment="关联创建时间"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], name="fk_dept_cert_type_dept_id"),
        sa.ForeignKeyConstraint(["certificate_type_id"], ["certificate_types.id"], name="fk_dept_cert_type_cert_id"),
        sa.PrimaryKeyConstraint("department_id", "certificate_type_id", name="pk_dept_cert_type"),
    )


def downgrade():
    # 删除关联表
    op.drop_table("department_certificate_types")
    
    # 删除证书类型表
    try:
        op.drop_index("ix_certificate_types_name", table_name="certificate_types")
    except Exception:
        pass
    op.drop_table("certificate_types")

