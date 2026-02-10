"""add_exchange_rate_history_and_product_prices

Revision ID: b203ca7e045c
Revises: e56421e59c92
Create Date: 2026-01-15 05:18:23.140113

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b203ca7e045c'
down_revision: Union[str, None] = 'e56421e59c92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ✅ Crear tabla exchange_rate_history
    op.create_table(
        'exchange_rate_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('from_currency_id', sa.Integer(), nullable=False),
        sa.Column('to_currency_id', sa.Integer(), nullable=False),
        sa.Column('rate', sa.Float(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['from_currency_id'], ['currencies.id'], ),
        sa.ForeignKeyConstraint(['to_currency_id'], ['currencies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exchange_rate_history_id'), 'exchange_rate_history', ['id'], unique=False)
    op.create_index(op.f('ix_exchange_rate_history_recorded_at'), 'exchange_rate_history', ['recorded_at'], unique=False)

    # ✅ Crear tabla product_prices
    op.create_table(
        'product_prices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('currency_id', sa.Integer(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('is_base_price', sa.Boolean(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['currency_id'], ['currencies.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_product_prices_id'), 'product_prices', ['id'], unique=False)

    # ✅ Agregar exchange_rate_date a invoices
    op.add_column('invoices', sa.Column('exchange_rate_date', sa.DateTime(), nullable=True))

    # ✅ Agregar exchange_rate_date a purchases
    op.add_column('purchases', sa.Column('exchange_rate_date', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # ✅ Eliminar exchange_rate_date de purchases
    op.drop_column('purchases', 'exchange_rate_date')

    # ✅ Eliminar exchange_rate_date de invoices
    op.drop_column('invoices', 'exchange_rate_date')

    # ✅ Eliminar tabla product_prices
    op.drop_index(op.f('ix_product_prices_id'), table_name='product_prices')
    op.drop_table('product_prices')

    # ✅ Eliminar tabla exchange_rate_history
    op.drop_index(op.f('ix_exchange_rate_history_recorded_at'), table_name='exchange_rate_history')
    op.drop_index(op.f('ix_exchange_rate_history_id'), table_name='exchange_rate_history')
    op.drop_table('exchange_rate_history')
