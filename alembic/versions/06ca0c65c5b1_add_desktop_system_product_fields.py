"""add_desktop_system_product_fields

Revision ID: 06ca0c65c5b1
Revises: 62ccf891a345
Create Date: 2026-01-18 15:21:27.683111

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '06ca0c65c5b1'
down_revision: Union[str, None] = '62ccf891a345'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ✅ SISTEMA ESCRITORIO: Agregar campos a la tabla products
    # Campos básicos
    op.add_column('products', sa.Column('short_name', sa.String(length=50), nullable=True))
    op.add_column('products', sa.Column('mark', sa.String(length=50), nullable=True))
    op.add_column('products', sa.Column('model', sa.String(length=50), nullable=True))
    op.add_column('products', sa.Column('department_id', sa.Integer(), nullable=True))
    op.add_column('products', sa.Column('size', sa.String(length=20), nullable=True))
    op.add_column('products', sa.Column('color', sa.String(length=30), nullable=True))
    op.add_column('products', sa.Column('product_type', sa.String(length=1), server_default='T', nullable=True))

    # Impuestos (códigos)
    op.add_column('products', sa.Column('sale_tax_code', sa.String(length=2), server_default='01', nullable=True))
    op.add_column('products', sa.Column('buy_tax_code', sa.String(length=2), server_default='01', nullable=True))

    # Precios múltiples
    op.add_column('products', sa.Column('maximum_price', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('products', sa.Column('offer_price', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('products', sa.Column('higher_price', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('products', sa.Column('minimum_price', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('products', sa.Column('sale_price_type', sa.Integer(), server_default='0', nullable=True))

    # Stock e inventario
    op.add_column('products', sa.Column('stock_quantity', sa.Integer(), server_default='0', nullable=True))
    op.add_column('products', sa.Column('maximum_stock', sa.Integer(), server_default='0', nullable=True))
    op.add_column('products', sa.Column('allow_negative_stock', sa.Boolean(), server_default='0', nullable=True))
    op.add_column('products', sa.Column('serialized', sa.Boolean(), server_default='0', nullable=True))
    op.add_column('products', sa.Column('use_lots', sa.Boolean(), server_default='0', nullable=True))
    op.add_column('products', sa.Column('lots_order', sa.Integer(), server_default='0', nullable=True))

    # Costeo
    op.add_column('products', sa.Column('costing_type', sa.Integer(), server_default='0', nullable=True))
    op.add_column('products', sa.Column('calculated_cost', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('products', sa.Column('average_cost', sa.Numeric(precision=10, scale=2), nullable=True))

    # Descuentos y límites
    op.add_column('products', sa.Column('discount', sa.Numeric(precision=5, scale=2), server_default='0', nullable=True))
    op.add_column('products', sa.Column('max_discount', sa.Numeric(precision=5, scale=2), server_default='0', nullable=True))
    op.add_column('products', sa.Column('minimal_sale', sa.Numeric(precision=10, scale=2), server_default='0', nullable=True))
    op.add_column('products', sa.Column('maximal_sale', sa.Numeric(precision=10, scale=2), server_default='0', nullable=True))

    # Configuraciones adicionales
    op.add_column('products', sa.Column('allow_decimal', sa.Boolean(), server_default='1', nullable=True))
    op.add_column('products', sa.Column('rounding_type', sa.Integer(), server_default='2', nullable=True))
    op.add_column('products', sa.Column('edit_name', sa.Boolean(), server_default='0', nullable=True))
    op.add_column('products', sa.Column('take_department_utility', sa.Boolean(), server_default='1', nullable=True))

    # Moneda
    op.add_column('products', sa.Column('coin', sa.String(length=2), server_default='01', nullable=True))

    # Garantía
    op.add_column('products', sa.Column('days_warranty', sa.Integer(), server_default='0', nullable=True))

    # Estado
    op.add_column('products', sa.Column('status', sa.String(length=2), server_default='01', nullable=True))

    # Crear foreign key para department_id
    op.create_foreign_key(
        'fk_products_department_id',
        'products', 'departments',
        ['department_id'], ['id']
    )

    # ✅ SISTEMA ESCRITORIO: Crear tabla product_units
    op.create_table(
        'product_units',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('correlative', sa.Integer(), nullable=False),
        sa.Column('unit_id', sa.Integer(), nullable=False),
        sa.Column('main_unit', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('conversion_factor', sa.Numeric(precision=10, scale=4), server_default='0', nullable=True),
        sa.Column('unit_type', sa.Integer(), server_default='1', nullable=True),
        sa.Column('show_in_screen', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('is_for_buy', sa.Boolean(), server_default='1', nullable=True),
        sa.Column('is_for_sale', sa.Boolean(), server_default='1', nullable=True),
        sa.Column('unitary_cost', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('calculated_cost', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('average_cost', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('perc_waste_cost', sa.Numeric(precision=5, scale=2), server_default='0', nullable=True),
        sa.Column('perc_handling_cost', sa.Numeric(precision=5, scale=2), server_default='0', nullable=True),
        sa.Column('perc_operating_cost', sa.Numeric(precision=5, scale=2), server_default='0', nullable=True),
        sa.Column('perc_additional_cost', sa.Numeric(precision=5, scale=2), server_default='0', nullable=True),
        sa.Column('maximum_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('offer_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('higher_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('minimum_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('perc_maximum_price', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('perc_offer_price', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('perc_higher_price', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('perc_minimum_price', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('perc_freight_cost', sa.Numeric(precision=5, scale=2), server_default='0', nullable=True),
        sa.Column('perc_discount_provider', sa.Numeric(precision=5, scale=2), server_default='0', nullable=True),
        sa.Column('lenght', sa.Numeric(precision=10, scale=2), server_default='0', nullable=True),
        sa.Column('height', sa.Numeric(precision=10, scale=2), server_default='0', nullable=True),
        sa.Column('width', sa.Numeric(precision=10, scale=2), server_default='0', nullable=True),
        sa.Column('weight', sa.Numeric(precision=10, scale=2), server_default='0', nullable=True),
        sa.Column('capacitance', sa.Numeric(precision=10, scale=2), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_product_units_id'), 'product_units', ['id'], unique=False)


def downgrade() -> None:
    # Eliminar tabla product_units
    op.drop_index(op.f('ix_product_units_id'), table_name='product_units')
    op.drop_table('product_units')

    # Eliminar foreign key
    op.drop_constraint('fk_products_department_id', 'products', type_='foreignkey')

    # Eliminar columnas de products (en orden inverso)
    op.drop_column('products', 'status')
    op.drop_column('products', 'days_warranty')
    op.drop_column('products', 'coin')
    op.drop_column('products', 'take_department_utility')
    op.drop_column('products', 'edit_name')
    op.drop_column('products', 'rounding_type')
    op.drop_column('products', 'allow_decimal')
    op.drop_column('products', 'maximal_sale')
    op.drop_column('products', 'minimal_sale')
    op.drop_column('products', 'max_discount')
    op.drop_column('products', 'discount')
    op.drop_column('products', 'average_cost')
    op.drop_column('products', 'calculated_cost')
    op.drop_column('products', 'costing_type')
    op.drop_column('products', 'lots_order')
    op.drop_column('products', 'use_lots')
    op.drop_column('products', 'serialized')
    op.drop_column('products', 'allow_negative_stock')
    op.drop_column('products', 'maximum_stock')
    op.drop_column('products', 'stock_quantity')
    op.drop_column('products', 'sale_price_type')
    op.drop_column('products', 'minimum_price')
    op.drop_column('products', 'higher_price')
    op.drop_column('products', 'offer_price')
    op.drop_column('products', 'maximum_price')
    op.drop_column('products', 'buy_tax_code')
    op.drop_column('products', 'sale_tax_code')
    op.drop_column('products', 'product_type')
    op.drop_column('products', 'color')
    op.drop_column('products', 'size')
    op.drop_column('products', 'department_id')
    op.drop_column('products', 'model')
    op.drop_column('products', 'mark')
    op.drop_column('products', 'short_name')
