"""add_desktop_system_customer_fields

Revision ID: ad1fda649c9e
Revises: 06ca0c65c5b1
Create Date: 2026-01-18 15:34:04.569022

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad1fda649c9e'
down_revision: Union[str, None] = '06ca0c65c5b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ✅ SISTEMA ESCRITORIO: Agregar campos a la tabla customers

    # Clasificación fiscal
    op.add_column('customers', sa.Column('name_fiscal', sa.Integer(), server_default='1', nullable=True))
    op.add_column('customers', sa.Column('client_type', sa.String(length=2), server_default='01', nullable=True))

    # Retenciones
    op.add_column('customers', sa.Column('retention_tax_agent', sa.Boolean(), server_default='0', nullable=True))
    op.add_column('customers', sa.Column('retention_municipal_agent', sa.Boolean(), server_default='0', nullable=True))
    op.add_column('customers', sa.Column('retention_islr_agent', sa.Boolean(), server_default='0', nullable=True))

    # Crédito
    op.add_column('customers', sa.Column('credit_days', sa.Integer(), server_default='0', nullable=True))
    op.add_column('customers', sa.Column('credit_limit', sa.Float(), server_default='0', nullable=True))
    op.add_column('customers', sa.Column('allow_expired_balance', sa.Boolean(), server_default='0', nullable=True))

    # Asignaciones
    op.add_column('customers', sa.Column('seller_id', sa.Integer(), nullable=True))
    op.add_column('customers', sa.Column('client_group_id', sa.Integer(), nullable=True))
    op.add_column('customers', sa.Column('area_sales_id', sa.Integer(), nullable=True))

    # Precios y descuentos
    op.add_column('customers', sa.Column('sale_price', sa.Integer(), server_default='1', nullable=True))
    op.add_column('customers', sa.Column('discount', sa.Float(), server_default='0', nullable=True))

    # Estado
    op.add_column('customers', sa.Column('status', sa.String(length=2), server_default='01', nullable=True))

    # Contacto adicional
    op.add_column('customers', sa.Column('contact_name', sa.String(length=100), nullable=True))

    # Crear foreign keys
    op.create_foreign_key(
        'fk_customers_seller_id',
        'customers', 'sellers',
        ['seller_id'], ['id']
    )
    op.create_foreign_key(
        'fk_customers_client_group_id',
        'customers', 'client_groups',
        ['client_group_id'], ['id']
    )
    op.create_foreign_key(
        'fk_customers_area_sales_id',
        'customers', 'areas_sales',
        ['area_sales_id'], ['id']
    )


def downgrade() -> None:
    # Eliminar foreign keys
    op.drop_constraint('fk_customers_area_sales_id', 'customers', type_='foreignkey')
    op.drop_constraint('fk_customers_client_group_id', 'customers', type_='foreignkey')
    op.drop_constraint('fk_customers_seller_id', 'customers', type_='foreignkey')

    # Eliminar columnas (en orden inverso)
    op.drop_column('customers', 'contact_name')
    op.drop_column('customers', 'status')
    op.drop_column('customers', 'discount')
    op.drop_column('customers', 'sale_price')
    op.drop_column('customers', 'area_sales_id')
    op.drop_column('customers', 'client_group_id')
    op.drop_column('customers', 'seller_id')
    op.drop_column('customers', 'allow_expired_balance')
    op.drop_column('customers', 'credit_limit')
    op.drop_column('customers', 'credit_days')
    op.drop_column('customers', 'retention_islr_agent')
    op.drop_column('customers', 'retention_municipal_agent')
    op.drop_column('customers', 'retention_tax_agent')
    op.drop_column('customers', 'client_type')
    op.drop_column('customers', 'name_fiscal')
