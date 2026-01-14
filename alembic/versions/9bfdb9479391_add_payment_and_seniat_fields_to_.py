"""add_payment_and_seniat_fields_to_purchases

Revision ID: 9bfdb9479391
Revises: 8951370b0191
Create Date: 2026-01-14 19:14:52.938414

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9bfdb9479391'
down_revision: Union[str, None] = '8951370b0191'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to purchases table
    op.add_column('purchases', sa.Column('invoice_number', sa.String(30), nullable=True))
    op.add_column('purchases', sa.Column('control_number', sa.String(20), nullable=True))
    op.add_column('purchases', sa.Column('due_date', sa.DateTime(), nullable=True))
    op.add_column('purchases', sa.Column('discount', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('purchases', sa.Column('notes', sa.Text(), nullable=True))

    # Payment and transaction fields
    op.add_column('purchases', sa.Column('transaction_type', sa.String(20), nullable=True, server_default='contado'))
    op.add_column('purchases', sa.Column('payment_method', sa.String(30), nullable=True))
    op.add_column('purchases', sa.Column('credit_days', sa.Integer(), nullable=True, server_default='0'))

    # Venezuela tax fields (IVA)
    op.add_column('purchases', sa.Column('iva_percentage', sa.Float(), nullable=True, server_default='16.0'))
    op.add_column('purchases', sa.Column('iva_amount', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('purchases', sa.Column('taxable_base', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('purchases', sa.Column('exempt_amount', sa.Float(), nullable=True, server_default='0.0'))

    # Retention fields
    op.add_column('purchases', sa.Column('iva_retention', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('purchases', sa.Column('iva_retention_percentage', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('purchases', sa.Column('islr_retention', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('purchases', sa.Column('islr_retention_percentage', sa.Float(), nullable=True, server_default='0.0'))

    # Stamp tax and totals
    op.add_column('purchases', sa.Column('stamp_tax', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('purchases', sa.Column('subtotal', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('purchases', sa.Column('total_with_taxes', sa.Float(), nullable=True, server_default='0.0'))

    # Credit note references
    op.add_column('purchases', sa.Column('reference_purchase_number', sa.String(30), nullable=True))
    op.add_column('purchases', sa.Column('reference_control_number', sa.String(20), nullable=True))
    op.add_column('purchases', sa.Column('refund_reason', sa.Text(), nullable=True))

    # Supplier contact info
    op.add_column('purchases', sa.Column('supplier_phone', sa.String(20), nullable=True))
    op.add_column('purchases', sa.Column('supplier_address', sa.String(300), nullable=True))

    # Add columns to purchase_items table
    op.add_column('purchase_items', sa.Column('tax_rate', sa.Float(), nullable=True, server_default='16.0'))
    op.add_column('purchase_items', sa.Column('tax_amount', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('purchase_items', sa.Column('is_exempt', sa.Boolean(), nullable=True, server_default='0'))


def downgrade() -> None:
    # Remove columns from purchase_items
    op.drop_column('purchase_items', 'is_exempt')
    op.drop_column('purchase_items', 'tax_amount')
    op.drop_column('purchase_items', 'tax_rate')

    # Remove columns from purchases (in reverse order)
    op.drop_column('purchases', 'supplier_address')
    op.drop_column('purchases', 'supplier_phone')
    op.drop_column('purchases', 'refund_reason')
    op.drop_column('purchases', 'reference_control_number')
    op.drop_column('purchases', 'reference_purchase_number')
    op.drop_column('purchases', 'total_with_taxes')
    op.drop_column('purchases', 'subtotal')
    op.drop_column('purchases', 'stamp_tax')
    op.drop_column('purchases', 'islr_retention_percentage')
    op.drop_column('purchases', 'islr_retention')
    op.drop_column('purchases', 'iva_retention_percentage')
    op.drop_column('purchases', 'iva_retention')
    op.drop_column('purchases', 'exempt_amount')
    op.drop_column('purchases', 'taxable_base')
    op.drop_column('purchases', 'iva_amount')
    op.drop_column('purchases', 'iva_percentage')
    op.drop_column('purchases', 'credit_days')
    op.drop_column('purchases', 'payment_method')
    op.drop_column('purchases', 'transaction_type')
    op.drop_column('purchases', 'notes')
    op.drop_column('purchases', 'discount')
    op.drop_column('purchases', 'due_date')
    op.drop_column('purchases', 'control_number')
    op.drop_column('purchases', 'invoice_number')
