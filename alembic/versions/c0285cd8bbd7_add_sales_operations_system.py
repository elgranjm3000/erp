"""add_sales_operations_system

Revision ID: c0285cd8bbd7
Revises: ad1fda649c9e
Create Date: 2026-01-18 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0285cd8bbd7'
down_revision: Union[str, None] = 'ad1fda649c9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ✅ SISTEMA ESCRITORIO: Tabla principal de operaciones de venta
    op.create_table(
        'sales_operations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('correlative', sa.Integer(), nullable=False),
        sa.Column('operation_type', sa.String(length=20), nullable=False),
        sa.Column('document_no', sa.String(length=50), nullable=True),
        sa.Column('document_no_internal', sa.String(length=50), server_default='', nullable=True),
        sa.Column('control_no', sa.String(length=50), nullable=True),
        sa.Column('emission_date', sa.DateTime(), nullable=False),
        sa.Column('register_date', sa.DateTime(), nullable=False),
        sa.Column('register_hour', sa.String(length=12), nullable=True),
        sa.Column('expiration_date', sa.DateTime(), nullable=True),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('client_name', sa.String(length=150), nullable=True),
        sa.Column('client_tax_id', sa.String(length=20), nullable=True),
        sa.Column('client_address', sa.String(length=300), nullable=True),
        sa.Column('client_phone', sa.String(length=20), nullable=True),
        sa.Column('client_name_fiscal', sa.Integer(), server_default='1', nullable=True),
        sa.Column('seller', sa.String(length=10), server_default='00', nullable=True),
        sa.Column('store', sa.String(length=10), server_default='00', nullable=True),
        sa.Column('locations', sa.String(length=10), server_default='00', nullable=True),
        sa.Column('user_code', sa.String(length=60), nullable=True),
        sa.Column('station', sa.String(length=10), server_default='00', nullable=True),
        sa.Column('wait', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('pending', sa.Boolean(), server_default='1', nullable=True),
        sa.Column('canceled', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('delivered', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('begin_used', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('total_amount', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_net_details', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_tax_details', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_details', sa.Float(), server_default='0', nullable=True),
        sa.Column('percent_discount', sa.Float(), server_default='0', nullable=True),
        sa.Column('discount', sa.Float(), server_default='0', nullable=True),
        sa.Column('percent_freight', sa.Float(), server_default='0', nullable=True),
        sa.Column('freight', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_net', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_tax', sa.Float(), server_default='0', nullable=True),
        sa.Column('total', sa.Float(), server_default='0', nullable=True),
        sa.Column('credit', sa.Float(), server_default='0', nullable=True),
        sa.Column('cash', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_net_cost', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_tax_cost', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_cost', sa.Float(), server_default='0', nullable=True),
        sa.Column('type_price', sa.Integer(), server_default='0', nullable=True),
        sa.Column('total_count_details', sa.Float(), server_default='0', nullable=True),
        sa.Column('freight_tax', sa.String(length=2), server_default='01', nullable=True),
        sa.Column('freight_aliquot', sa.Float(), server_default='16', nullable=True),
        sa.Column('total_retention_tax', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_retention_municipal', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_retention_islr', sa.Float(), server_default='0', nullable=True),
        sa.Column('retention_tax_prorration', sa.Float(), server_default='0', nullable=True),
        sa.Column('retention_islr_prorration', sa.Float(), server_default='0', nullable=True),
        sa.Column('retention_municipal_prorration', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_operation', sa.Float(), server_default='0', nullable=True),
        sa.Column('fiscal_impresion', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('fiscal_printer_serial', sa.String(length=50), server_default='', nullable=True),
        sa.Column('fiscal_printer_z', sa.String(length=50), server_default='', nullable=True),
        sa.Column('fiscal_printer_date', sa.DateTime(), nullable=True),
        sa.Column('coin_code', sa.String(length=2), server_default='01', nullable=True),
        sa.Column('sale_point', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('restorant', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('address_send', sa.String(length=300), server_default='', nullable=True),
        sa.Column('contact_send', sa.String(length=100), server_default='', nullable=True),
        sa.Column('phone_send', sa.String(length=20), server_default='', nullable=True),
        sa.Column('total_weight', sa.Float(), server_default='0', nullable=True),
        sa.Column('free_tax', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('total_exempt', sa.Float(), server_default='0', nullable=True),
        sa.Column('base_igtf', sa.Float(), server_default='0', nullable=True),
        sa.Column('percent_igtf', sa.Float(), server_default='0', nullable=True),
        sa.Column('igtf', sa.Float(), server_default='0', nullable=True),
        sa.Column('shopping_order_document_no', sa.String(length=50), server_default='', nullable=True),
        sa.Column('shopping_order_date', sa.DateTime(), nullable=True),
        sa.Column('operation_comments', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['client_id'], ['customers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sales_operations_id'), 'sales_operations', ['id'], unique=False)

    # ✅ SISTEMA ESCRITORIO: Montos en diferentes monedas
    op.create_table(
        'sales_operation_coins',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('sales_operation_id', sa.Integer(), nullable=False),
        sa.Column('main_correlative', sa.Integer(), nullable=False),
        sa.Column('coin_code', sa.String(length=2), nullable=False),
        sa.Column('factor_type', sa.Integer(), nullable=False),
        sa.Column('buy_aliquot', sa.Float(), nullable=False),
        sa.Column('sales_aliquot', sa.Float(), nullable=False),
        sa.Column('total_net_details', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_tax_details', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_details', sa.Float(), server_default='0', nullable=True),
        sa.Column('discount', sa.Float(), server_default='0', nullable=True),
        sa.Column('freight', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_net', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_tax', sa.Float(), server_default='0', nullable=True),
        sa.Column('total', sa.Float(), server_default='0', nullable=True),
        sa.Column('credit', sa.Float(), server_default='0', nullable=True),
        sa.Column('cash', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_net_cost', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_tax_cost', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_cost', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_operation', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_retention_tax', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_retention_municipal', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_retention_islr', sa.Float(), server_default='0', nullable=True),
        sa.Column('retention_tax_prorration', sa.Float(), server_default='0', nullable=True),
        sa.Column('retention_islr_prorration', sa.Float(), server_default='0', nullable=True),
        sa.Column('retention_municipal_prorration', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_exempt', sa.Float(), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['sales_operation_id'], ['sales_operations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sales_operation_coins_id'), 'sales_operation_coins', ['id'], unique=False)

    # ✅ SISTEMA ESCRITORIO: Detalles de la operación (líneas)
    op.create_table(
        'sales_operation_details',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('sales_operation_id', sa.Integer(), nullable=False),
        sa.Column('main_correlative', sa.Integer(), nullable=False),
        sa.Column('line', sa.Integer(), nullable=False),
        sa.Column('code_product', sa.String(length=50), nullable=True),
        sa.Column('description_product', sa.String(length=200), nullable=True),
        sa.Column('referenc', sa.String(length=50), nullable=True),
        sa.Column('mark', sa.String(length=50), nullable=True),
        sa.Column('model', sa.String(length=50), nullable=True),
        sa.Column('store', sa.String(length=10), nullable=True),
        sa.Column('locations', sa.String(length=10), nullable=True),
        sa.Column('unit', sa.Integer(), nullable=True),
        sa.Column('conversion_factor', sa.Float(), server_default='0', nullable=True),
        sa.Column('unit_type', sa.Integer(), server_default='0', nullable=True),
        sa.Column('amount', sa.Float(), server_default='0', nullable=True),
        sa.Column('unitary_cost', sa.Float(), server_default='0', nullable=True),
        sa.Column('sale_tax', sa.String(length=2), server_default='01', nullable=True),
        sa.Column('sale_aliquot', sa.Float(), server_default='0', nullable=True),
        sa.Column('price', sa.Float(), server_default='0', nullable=True),
        sa.Column('type_price', sa.Integer(), server_default='0', nullable=True),
        sa.Column('total_net_cost', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_tax_cost', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_cost', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_net_gross', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_tax_gross', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_gross', sa.Float(), server_default='0', nullable=True),
        sa.Column('percent_discount', sa.Float(), server_default='0', nullable=True),
        sa.Column('discount', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_net', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_tax', sa.Float(), server_default='0', nullable=True),
        sa.Column('total', sa.Float(), server_default='0', nullable=True),
        sa.Column('pending_amount', sa.Float(), server_default='0', nullable=True),
        sa.Column('buy_tax', sa.String(length=2), server_default='01', nullable=True),
        sa.Column('buy_aliquot', sa.Float(), server_default='0', nullable=True),
        sa.Column('update_inventory', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('amount_released_by_load_order', sa.Float(), server_default='0', nullable=True),
        sa.Column('amount_discharged_by_load_delivery_note', sa.Float(), server_default='0', nullable=True),
        sa.Column('product_type', sa.String(length=1), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('technician', sa.String(length=10), server_default='00', nullable=True),
        sa.Column('coin_code', sa.String(length=2), server_default='01', nullable=True),
        sa.Column('total_weight', sa.Float(), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['sales_operation_id'], ['sales_operations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sales_operation_details_id'), 'sales_operation_details', ['id'], unique=False)

    # ✅ SISTEMA ESCRITORIO: Montos de detalles en diferentes monedas
    op.create_table(
        'sales_operation_detail_coins',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('main_correlative', sa.Integer(), nullable=False),
        sa.Column('main_line', sa.Integer(), nullable=False),
        sa.Column('coin_code', sa.String(length=2), nullable=False),
        sa.Column('unitary_cost', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_net_cost', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_tax_cost', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_cost', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_net_gross', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_tax_gross', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_gross', sa.Float(), server_default='0', nullable=True),
        sa.Column('discount', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_net', sa.Float(), server_default='0', nullable=True),
        sa.Column('total_tax', sa.Float(), server_default='0', nullable=True),
        sa.Column('total', sa.Float(), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sales_operation_detail_coins_id'), 'sales_operation_detail_coins', ['id'], unique=False)

    # ✅ SISTEMA ESCRITORIO: Impuestos del documento
    op.create_table(
        'sales_operation_taxes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('sales_operation_id', sa.Integer(), nullable=False),
        sa.Column('main_correlative', sa.Integer(), nullable=False),
        sa.Column('line', sa.Integer(), nullable=False),
        sa.Column('taxe_code', sa.String(length=10), nullable=False),
        sa.Column('aliquot', sa.Float(), nullable=False),
        sa.Column('taxable', sa.Float(), server_default='0', nullable=True),
        sa.Column('tax', sa.Float(), server_default='0', nullable=True),
        sa.Column('tax_type', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['sales_operation_id'], ['sales_operations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sales_operation_taxes_id'), 'sales_operation_taxes', ['id'], unique=False)

    # ✅ SISTEMA ESCRITORIO: Impuestos en diferentes monedas
    op.create_table(
        'sales_operation_tax_coins',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('main_correlative', sa.Integer(), nullable=False),
        sa.Column('main_taxe_code', sa.String(length=10), nullable=False),
        sa.Column('main_line', sa.Integer(), nullable=False),
        sa.Column('coin_code', sa.String(length=2), nullable=False),
        sa.Column('taxable', sa.Float(), server_default='0', nullable=True),
        sa.Column('tax', sa.Float(), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sales_operation_tax_coins_id'), 'sales_operation_tax_coins', ['id'], unique=False)


def downgrade() -> None:
    # Eliminar tablas en orden inverso
    op.drop_index(op.f('ix_sales_operation_tax_coins_id'), table_name='sales_operation_tax_coins')
    op.drop_table('sales_operation_tax_coins')

    op.drop_index(op.f('ix_sales_operation_taxes_id'), table_name='sales_operation_taxes')
    op.drop_table('sales_operation_taxes')

    op.drop_index(op.f('ix_sales_operation_detail_coins_id'), table_name='sales_operation_detail_coins')
    op.drop_table('sales_operation_detail_coins')

    op.drop_index(op.f('ix_sales_operation_details_id'), table_name='sales_operation_details')
    op.drop_table('sales_operation_details')

    op.drop_index(op.f('ix_sales_operation_coins_id'), table_name='sales_operation_coins')
    op.drop_table('sales_operation_coins')

    op.drop_index(op.f('ix_sales_operations_id'), table_name='sales_operations')
    op.drop_table('sales_operations')
