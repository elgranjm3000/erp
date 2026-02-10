"""Expand coin_code to varchar(3) in sales operations

Revision ID: b36ff28f0994
Revises: 461d2c6613d0
Create Date: 2026-01-18 18:57:13.927526

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b36ff28f0994'
down_revision: Union[str, None] = '461d2c6613d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Expandir coin_code de VARCHAR(2) a VARCHAR(3) en todas las tablas de sales_operations
    op.alter_column('sales_operations',
                    'coin_code',
                    existing_type=sa.VARCHAR(length=2),
                    type_=sa.VARCHAR(length=3),
                    existing_nullable=False)

    op.alter_column('sales_operation_coins',
                    'coin_code',
                    existing_type=sa.VARCHAR(length=2),
                    type_=sa.VARCHAR(length=3),
                    existing_nullable=False)

    op.alter_column('sales_operation_detail_coins',
                    'coin_code',
                    existing_type=sa.VARCHAR(length=2),
                    type_=sa.VARCHAR(length=3),
                    existing_nullable=False)

    op.alter_column('sales_operation_tax_coins',
                    'coin_code',
                    existing_type=sa.VARCHAR(length=2),
                    type_=sa.VARCHAR(length=3),
                    existing_nullable=False)


def downgrade() -> None:
    # Revertir a VARCHAR(2)
    op.alter_column('sales_operation_tax_coins',
                    'coin_code',
                    existing_type=sa.VARCHAR(length=3),
                    type_=sa.VARCHAR(length=2),
                    existing_nullable=False)

    op.alter_column('sales_operation_detail_coins',
                    'coin_code',
                    existing_type=sa.VARCHAR(length=3),
                    type_=sa.VARCHAR(length=2),
                    existing_nullable=False)

    op.alter_column('sales_operation_coins',
                    'coin_code',
                    existing_type=sa.VARCHAR(length=3),
                    type_=sa.VARCHAR(length=2),
                    existing_nullable=False)

    op.alter_column('sales_operations',
                    'coin_code',
                    existing_type=sa.VARCHAR(length=3),
                    type_=sa.VARCHAR(length=2),
                    existing_nullable=False)
