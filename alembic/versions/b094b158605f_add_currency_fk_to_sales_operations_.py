"""add_currency_fk_to_sales_operations_coins

Revision ID: b094b158605f
Revises: 7e3cbf82afb4
Create Date: 2026-01-18 22:24:37.882406

✅ SISTEMA ESCRITORIO: Agrega FK a currencies y expande coin_code a VARCHAR(3)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b094b158605f'
down_revision: Union[str, None] = '7e3cbf82afb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==================== ✅ SALES_OPERATION_COINS ====================

    # Expandir coin_code de VARCHAR(2) a VARCHAR(3)
    op.alter_column('sales_operation_coins',
                    'coin_code',
                    existing_type=sa.VARCHAR(length=2),
                    type_=sa.VARCHAR(length=3),
                    nullable=False)

    # Agregar currency_id con FK a currencies
    op.add_column('sales_operation_coins',
                  sa.Column('currency_id',
                            sa.Integer(),
                            nullable=True))

    op.create_foreign_key(
        'fk_sales_operation_coins_currency_id',
        'sales_operation_coins', 'currencies',
        ['currency_id'], ['id']
    )

    # ==================== ✅ SALES_OPERATION_DETAIL_COINS ====================

    # Expandir coin_code de VARCHAR(2) a VARCHAR(3)
    op.alter_column('sales_operation_detail_coins',
                    'coin_code',
                    existing_type=sa.VARCHAR(length=2),
                    type_=sa.VARCHAR(length=3),
                    nullable=False)

    # Agregar currency_id con FK a currencies
    op.add_column('sales_operation_detail_coins',
                  sa.Column('currency_id',
                            sa.Integer(),
                            nullable=True))

    op.create_foreign_key(
        'fk_sales_operation_detail_coins_currency_id',
        'sales_operation_detail_coins', 'currencies',
        ['currency_id'], ['id']
    )

    # ==================== ✅ SALES_OPERATION_TAX_COINS ====================

    # Expandir coin_code de VARCHAR(2) a VARCHAR(3)
    op.alter_column('sales_operation_tax_coins',
                    'coin_code',
                    existing_type=sa.VARCHAR(length=2),
                    type_=sa.VARCHAR(length=3),
                    nullable=False)

    # Agregar currency_id con FK a currencies
    op.add_column('sales_operation_tax_coins',
                  sa.Column('currency_id',
                            sa.Integer(),
                            nullable=True))

    op.create_foreign_key(
        'fk_sales_operation_tax_coins_currency_id',
        'sales_operation_tax_coins', 'currencies',
        ['currency_id'], ['id']
    )


def downgrade() -> None:
    # ==================== ✅ REVERT SALES_OPERATION_TAX_COINS ====================

    op.drop_constraint('fk_sales_operation_tax_coins_currency_id', 'sales_operation_tax_coins')
    op.drop_column('sales_operation_tax_coins', 'currency_id')

    op.alter_column('sales_operation_tax_coins',
                    'coin_code',
                    existing_type=sa.VARCHAR(length=3),
                    type_=sa.VARCHAR(length=2),
                    nullable=False)

    # ==================== ✅ REVERT SALES_OPERATION_DETAIL_COINS ====================

    op.drop_constraint('fk_sales_operation_detail_coins_currency_id', 'sales_operation_detail_coins')
    op.drop_column('sales_operation_detail_coins', 'currency_id')

    op.alter_column('sales_operation_detail_coins',
                    'coin_code',
                    existing_type=sa.VARCHAR(length=3),
                    type_=sa.VARCHAR(length=2),
                    nullable=False)

    # ==================== ✅ REVERT SALES_OPERATION_COINS ====================

    op.drop_constraint('fk_sales_operation_coins_currency_id', 'sales_operation_coins')
    op.drop_column('sales_operation_coins', 'currency_id')

    op.alter_column('sales_operation_coins',
                    'coin_code',
                    existing_type=sa.VARCHAR(length=3),
                    type_=sa.VARCHAR(length=2),
                    nullable=False)

