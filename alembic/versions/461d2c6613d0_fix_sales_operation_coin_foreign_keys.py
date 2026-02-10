"""Fix sales operation coin foreign keys

Revision ID: 461d2c6613d0
Revises: c0285cd8bbd7
Create Date: 2026-01-18 17:26:49.382121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '461d2c6613d0'
down_revision: Union[str, None] = 'c0285cd8bbd7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add foreign key column to sales_operation_detail_coins
    op.add_column('sales_operation_detail_coins',
                  sa.Column('sales_operation_detail_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_sales_operation_detail_coins_detail_id',
        'sales_operation_detail_coins', 'sales_operation_details',
        ['sales_operation_detail_id'], ['id']
    )

    # Add foreign key column to sales_operation_tax_coins
    op.add_column('sales_operation_tax_coins',
                  sa.Column('sales_operation_tax_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_sales_operation_tax_coins_tax_id',
        'sales_operation_tax_coins', 'sales_operation_taxes',
        ['sales_operation_tax_id'], ['id']
    )


def downgrade() -> None:
    # Remove foreign keys and columns
    op.drop_constraint('fk_sales_operation_tax_coins_tax_id',
                       'sales_operation_tax_coins', type_='foreignkey')
    op.drop_column('sales_operation_tax_coins', 'sales_operation_tax_id')

    op.drop_constraint('fk_sales_operation_detail_coins_detail_id',
                       'sales_operation_detail_coins', type_='foreignkey')
    op.drop_column('sales_operation_detail_coins', 'sales_operation_detail_id')
