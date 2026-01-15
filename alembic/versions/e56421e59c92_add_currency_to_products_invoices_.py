"""add_currency_to_products_invoices_purchases

Revision ID: e56421e59c92
Revises: 20d31c25f1ef
Create Date: 2026-01-14 23:12:28.808324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e56421e59c92'
down_revision: Union[str, None] = '20d31c25f1ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ✅ Add currency_id to products
    op.add_column('products', sa.Column('currency_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_products_currency_id', 'products', 'currencies', ['currency_id'], ['id'])

    # ✅ Change price from Integer to Float
    op.alter_column('products', 'price',
                   existing_type=sa.Integer(),
                   type_=sa.Float())

    # ✅ Add currency_id and exchange_rate to invoices
    op.add_column('invoices', sa.Column('currency_id', sa.Integer(), nullable=True))
    op.add_column('invoices', sa.Column('exchange_rate', sa.Float(), nullable=True))
    op.create_foreign_key('fk_invoices_currency_id', 'invoices', 'currencies', ['currency_id'], ['id'])

    # ✅ Add currency_id and exchange_rate to purchases
    op.add_column('purchases', sa.Column('currency_id', sa.Integer(), nullable=True))
    op.add_column('purchases', sa.Column('exchange_rate', sa.Float(), nullable=True))
    op.create_foreign_key('fk_purchases_currency_id', 'purchases', 'currencies', ['currency_id'], ['id'])


def downgrade() -> None:
    # ✅ Remove from purchases
    op.drop_constraint('fk_purchases_currency_id', 'purchases', type_='foreignkey')
    op.drop_column('purchases', 'exchange_rate')
    op.drop_column('purchases', 'currency_id')

    # ✅ Remove from invoices
    op.drop_constraint('fk_invoices_currency_id', 'invoices', type_='foreignkey')
    op.drop_column('invoices', 'exchange_rate')
    op.drop_column('invoices', 'currency_id')

    # ✅ Revert price to Integer
    op.alter_column('products', 'price',
                   existing_type=sa.Float(),
                   type_=sa.Integer())

    # ✅ Remove from products
    op.drop_constraint('fk_products_currency_id', 'products', type_='foreignkey')
    op.drop_column('products', 'currency_id')
