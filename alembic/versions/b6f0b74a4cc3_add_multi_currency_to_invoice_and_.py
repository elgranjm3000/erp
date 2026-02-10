"""add_multi_currency_to_invoice_and_purchase_items

Revision ID: b6f0b74a4cc3
Revises: b203ca7e045c
Create Date: 2026-01-15 05:45:11.515529

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b6f0b74a4cc3'
down_revision: Union[str, None] = 'b203ca7e045c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ✅ Agregar campos multi-moneda a invoice_items
    op.add_column('invoice_items', sa.Column('currency_id', sa.Integer(), nullable=True))
    op.add_column('invoice_items', sa.Column('exchange_rate', sa.Float(), nullable=True))
    op.add_column('invoice_items', sa.Column('exchange_rate_date', sa.DateTime(), nullable=True))
    op.add_column('invoice_items', sa.Column('base_currency_amount', sa.Float(), nullable=True, server_default='0.0'))

    # Foreign key para currency_id en invoice_items
    op.create_foreign_key(
        'fk_invoice_items_currency_id',
        'invoice_items', 'currencies',
        ['currency_id'], ['id']
    )

    # ✅ Agregar campos multi-moneda a purchase_items
    op.add_column('purchase_items', sa.Column('currency_id', sa.Integer(), nullable=True))
    op.add_column('purchase_items', sa.Column('exchange_rate', sa.Float(), nullable=True))
    op.add_column('purchase_items', sa.Column('exchange_rate_date', sa.DateTime(), nullable=True))
    op.add_column('purchase_items', sa.Column('base_currency_amount', sa.Float(), nullable=True, server_default='0.0'))

    # Foreign key para currency_id en purchase_items
    op.create_foreign_key(
        'fk_purchase_items_currency_id',
        'purchase_items', 'currencies',
        ['currency_id'], ['id']
    )


def downgrade() -> None:
    # ✅ Eliminar campos de purchase_items
    op.drop_constraint('fk_purchase_items_currency_id', 'purchase_items', type_='foreignkey')
    op.drop_column('purchase_items', 'base_currency_amount')
    op.drop_column('purchase_items', 'exchange_rate_date')
    op.drop_column('purchase_items', 'exchange_rate')
    op.drop_column('purchase_items', 'currency_id')

    # ✅ Eliminar campos de invoice_items
    op.drop_constraint('fk_invoice_items_currency_id', 'invoice_items', type_='foreignkey')
    op.drop_column('invoice_items', 'base_currency_amount')
    op.drop_column('invoice_items', 'exchange_rate_date')
    op.drop_column('invoice_items', 'exchange_rate')
    op.drop_column('invoice_items', 'currency_id')
