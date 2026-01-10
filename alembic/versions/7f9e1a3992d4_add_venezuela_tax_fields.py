"""add_venezuela_tax_fields

Revision ID: 7f9e1a3992d4
Revises: e99c6812febf
Create Date: 2026-01-10 16:57:37.406252

Agregar campos para facturación en Venezuela según normativa SENIAT:
- Número de control
- IVA (16%, 8%, exento)
- Retenciones (IVA y ISLR)
- Timado fiscal
- Datos fiscales de empresa
- Información de transacciones

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f9e1a3992d4'
down_revision: Union[str, None] = 'e99c6812febf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Obtener conexión para ejecutar SQL directo
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Verificar columnas existentes
    companies_columns = [col['name'] for col in inspector.get_columns('companies')]
    invoices_columns = [col['name'] for col in inspector.get_columns('invoices')]
    invoice_items_columns = [col['name'] for col in inspector.get_columns('invoice_items')]

    # ================= COMPANIES =================
    # Agregar campos de facturación y control solo si no existen
    if 'next_control_number' not in companies_columns:
        op.add_column('companies', sa.Column('next_control_number', sa.Integer(), nullable=True, server_default='1'))
    if 'fiscal_address' not in companies_columns:
        op.add_column('companies', sa.Column('fiscal_address', sa.String(300), nullable=True))
    if 'taxpayer_type' not in companies_columns:
        op.add_column('companies', sa.Column('taxpayer_type', sa.String(20), nullable=True, server_default='ordinario'))
    if 'seniat_certificate_number' not in companies_columns:
        op.add_column('companies', sa.Column('seniat_certificate_number', sa.String(30), nullable=True))
    if 'iva_retention_agent' not in companies_columns:
        op.add_column('companies', sa.Column('iva_retention_agent', sa.Boolean(), nullable=True, server_default='0'))
    if 'islr_retention_agent' not in companies_columns:
        op.add_column('companies', sa.Column('islr_retention_agent', sa.Boolean(), nullable=True, server_default='0'))
    if 'invoice_contact_name' not in companies_columns:
        op.add_column('companies', sa.Column('invoice_contact_name', sa.String(100), nullable=True))
    if 'invoice_contact_phone' not in companies_columns:
        op.add_column('companies', sa.Column('invoice_contact_phone', sa.String(20), nullable=True))
    if 'invoice_contact_email' not in companies_columns:
        op.add_column('companies', sa.Column('invoice_contact_email', sa.String(100), nullable=True))
    if 'iva_retention_rate_75' not in companies_columns:
        op.add_column('companies', sa.Column('iva_retention_rate_75', sa.Float(), nullable=True, server_default='75.0'))
    if 'iva_retention_rate_100' not in companies_columns:
        op.add_column('companies', sa.Column('iva_retention_rate_100', sa.Float(), nullable=True, server_default='100.0'))
    if 'islr_retention_rate_1' not in companies_columns:
        op.add_column('companies', sa.Column('islr_retention_rate_1', sa.Float(), nullable=True, server_default='1.0'))
    if 'islr_retention_rate_2' not in companies_columns:
        op.add_column('companies', sa.Column('islr_retention_rate_2', sa.Float(), nullable=True, server_default='2.0'))
    if 'islr_retention_rate_3' not in companies_columns:
        op.add_column('companies', sa.Column('islr_retention_rate_3', sa.Float(), nullable=True, server_default='3.0'))

    # ================= INVOICES =================
    # Agregar campos de control y numeración solo si no existen
    if 'control_number' not in invoices_columns:
        op.add_column('invoices', sa.Column('control_number', sa.String(20), nullable=True))

    # Agregar campos de información fiscal
    if 'transaction_type' not in invoices_columns:
        op.add_column('invoices', sa.Column('transaction_type', sa.String(20), nullable=True, server_default='contado'))
    if 'payment_method' not in invoices_columns:
        op.add_column('invoices', sa.Column('payment_method', sa.String(30), nullable=True))
    if 'credit_days' not in invoices_columns:
        op.add_column('invoices', sa.Column('credit_days', sa.Integer(), nullable=True, server_default='0'))

    # Agregar campos de IVA
    if 'iva_percentage' not in invoices_columns:
        op.add_column('invoices', sa.Column('iva_percentage', sa.Float(), nullable=True, server_default='16.0'))
    if 'iva_amount' not in invoices_columns:
        op.add_column('invoices', sa.Column('iva_amount', sa.Float(), nullable=True, server_default='0.0'))
    if 'taxable_base' not in invoices_columns:
        op.add_column('invoices', sa.Column('taxable_base', sa.Float(), nullable=True, server_default='0.0'))
    if 'exempt_amount' not in invoices_columns:
        op.add_column('invoices', sa.Column('exempt_amount', sa.Float(), nullable=True, server_default='0.0'))

    # Agregar campos de retenciones
    if 'iva_retention' not in invoices_columns:
        op.add_column('invoices', sa.Column('iva_retention', sa.Float(), nullable=True, server_default='0.0'))
    if 'iva_retention_percentage' not in invoices_columns:
        op.add_column('invoices', sa.Column('iva_retention_percentage', sa.Float(), nullable=True, server_default='0.0'))
    if 'islr_retention' not in invoices_columns:
        op.add_column('invoices', sa.Column('islr_retention', sa.Float(), nullable=True, server_default='0.0'))
    if 'islr_retention_percentage' not in invoices_columns:
        op.add_column('invoices', sa.Column('islr_retention_percentage', sa.Float(), nullable=True, server_default='0.0'))

    # Agregar campo de timado fiscal
    if 'stamp_tax' not in invoices_columns:
        op.add_column('invoices', sa.Column('stamp_tax', sa.Float(), nullable=True, server_default='0.0'))

    # Agregar totales desglosados
    if 'subtotal' not in invoices_columns:
        op.add_column('invoices', sa.Column('subtotal', sa.Float(), nullable=True, server_default='0.0'))
    if 'total_with_taxes' not in invoices_columns:
        op.add_column('invoices', sa.Column('total_with_taxes', sa.Float(), nullable=True, server_default='0.0'))

    # Agregar campos para notas de crédito/débito
    if 'reference_invoice_number' not in invoices_columns:
        op.add_column('invoices', sa.Column('reference_invoice_number', sa.String(30), nullable=True))
    if 'reference_control_number' not in invoices_columns:
        op.add_column('invoices', sa.Column('reference_control_number', sa.String(20), nullable=True))
    if 'refund_reason' not in invoices_columns:
        op.add_column('invoices', sa.Column('refund_reason', sa.Text(), nullable=True))

    # Agregar información de contacto del cliente
    if 'customer_phone' not in invoices_columns:
        op.add_column('invoices', sa.Column('customer_phone', sa.String(20), nullable=True))
    if 'customer_address' not in invoices_columns:
        op.add_column('invoices', sa.Column('customer_address', sa.String(300), nullable=True))

    # ================= INVOICE ITEMS =================
    # Agregar campos de impuestos por item solo si no existen
    if 'tax_rate' not in invoice_items_columns:
        op.add_column('invoice_items', sa.Column('tax_rate', sa.Float(), nullable=True, server_default='16.0'))
    if 'tax_amount' not in invoice_items_columns:
        op.add_column('invoice_items', sa.Column('tax_amount', sa.Float(), nullable=True, server_default='0.0'))
    if 'is_exempt' not in invoice_items_columns:
        op.add_column('invoice_items', sa.Column('is_exempt', sa.Boolean(), nullable=True, server_default='0'))

    # Crear índices para búsquedas solo si no existe
    indexes = inspector.get_indexes('invoices')
    index_names = [idx['name'] for idx in indexes]
    if 'ix_invoices_control_number' not in index_names:
        op.create_index('ix_invoices_control_number', 'invoices', ['control_number'])


def downgrade() -> None:
    # ================= INVOICE ITEMS =================
    op.drop_index('ix_invoices_control_number', table_name='invoices')
    op.drop_column('invoice_items', 'is_exempt')
    op.drop_column('invoice_items', 'tax_amount')
    op.drop_column('invoice_items', 'tax_rate')

    # ================= INVOICES =================
    op.drop_column('invoices', 'customer_address')
    op.drop_column('invoices', 'customer_phone')
    op.drop_column('invoices', 'refund_reason')
    op.drop_column('invoices', 'reference_control_number')
    op.drop_column('invoices', 'reference_invoice_number')
    op.drop_column('invoices', 'total_with_taxes')
    op.drop_column('invoices', 'subtotal')
    op.drop_column('invoices', 'stamp_tax')
    op.drop_column('invoices', 'islr_retention_percentage')
    op.drop_column('invoices', 'islr_retention')
    op.drop_column('invoices', 'iva_retention_percentage')
    op.drop_column('invoices', 'iva_retention')
    op.drop_column('invoices', 'exempt_amount')
    op.drop_column('invoices', 'taxable_base')
    op.drop_column('invoices', 'iva_amount')
    op.drop_column('invoices', 'iva_percentage')
    op.drop_column('invoices', 'credit_days')
    op.drop_column('invoices', 'payment_method')
    op.drop_column('invoices', 'transaction_type')
    op.drop_column('invoices', 'control_number')

    # ================= COMPANIES =================
    op.drop_column('companies', 'islr_retention_rate_3')
    op.drop_column('companies', 'islr_retention_rate_2')
    op.drop_column('companies', 'islr_retention_rate_1')
    op.drop_column('companies', 'iva_retention_rate_100')
    op.drop_column('companies', 'iva_retention_rate_75')
    op.drop_column('companies', 'invoice_contact_email')
    op.drop_column('companies', 'invoice_contact_phone')
    op.drop_column('companies', 'invoice_contact_name')
    op.drop_column('companies', 'islr_retention_agent')
    op.drop_column('companies', 'iva_retention_agent')
    op.drop_column('companies', 'seniat_certificate_number')
    op.drop_column('companies', 'taxpayer_type')
    op.drop_column('companies', 'fiscal_address')
    op.drop_column('companies', 'next_control_number')
