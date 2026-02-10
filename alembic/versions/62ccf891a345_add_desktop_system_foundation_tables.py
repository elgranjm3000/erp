"""add_desktop_system_foundation_tables

Revision ID: 62ccf891a345
Revises: caa9e2cefd34
Create Date: 2026-01-18 15:16:12.117729

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62ccf891a345'
down_revision: Union[str, None] = 'caa9e2cefd34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ✅ SISTEMA ESCRITORIO: Tabla de departamentos
    op.create_table(
        'departments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.Column('utility_percentage', sa.Float(), nullable=True, server_default='30.0'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_departments_code'), 'departments', ['code'], unique=True)
    op.create_index(op.f('ix_departments_id'), 'departments', ['id'], unique=False)

    # ✅ SISTEMA ESCRITORIO: Tabla de vendedores
    op.create_table(
        'sellers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=2), nullable=True, server_default='01'),
        sa.Column('percent_sales', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('percent_receivable', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('user_code', sa.String(length=60), nullable=True),
        sa.Column('percent_gerencial_debit_note', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('percent_gerencial_credit_note', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('percent_returned_check', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['user_code'], ['users.username'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sellers_code'), 'sellers', ['code'], unique=True)
    op.create_index(op.f('ix_sellers_id'), 'sellers', ['id'], unique=False)

    # ✅ SISTEMA ESCRITORIO: Tabla de grupos de clientes
    op.create_table(
        'client_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_client_groups_code'), 'client_groups', ['code'], unique=True)
    op.create_index(op.f('ix_client_groups_id'), 'client_groups', ['id'], unique=False)

    # ✅ SISTEMA ESCRITORIO: Tabla de áreas de ventas
    op.create_table(
        'areas_sales',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_areas_sales_code'), 'areas_sales', ['code'], unique=True)
    op.create_index(op.f('ix_areas_sales_id'), 'areas_sales', ['id'], unique=False)

    # ✅ SISTEMA ESCRITORIO: Tabla de tipos de impuestos
    op.create_table(
        'tax_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.Column('aliquot', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tax_types_code'), 'tax_types', ['code'], unique=True)
    op.create_index(op.f('ix_tax_types_id'), 'tax_types', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tax_types_id'), table_name='tax_types')
    op.drop_index(op.f('ix_tax_types_code'), table_name='tax_types')
    op.drop_table('tax_types')

    op.drop_index(op.f('ix_areas_sales_id'), table_name='areas_sales')
    op.drop_index(op.f('ix_areas_sales_code'), table_name='areas_sales')
    op.drop_table('areas_sales')

    op.drop_index(op.f('ix_client_groups_id'), table_name='client_groups')
    op.drop_index(op.f('ix_client_groups_code'), table_name='client_groups')
    op.drop_table('client_groups')

    op.drop_index(op.f('ix_sellers_id'), table_name='sellers')
    op.drop_index(op.f('ix_sellers_code'), table_name='sellers')
    op.drop_table('sellers')

    op.drop_index(op.f('ix_departments_id'), table_name='departments')
    op.drop_index(op.f('ix_departments_code'), table_name='departments')
    op.drop_table('departments')
