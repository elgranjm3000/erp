"""add_purchase_credit_movement_model

Revision ID: 17dcde0a4aa9
Revises: 9bfdb9479391
Create Date: 2026-01-14 19:19:09.663693

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17dcde0a4aa9'
down_revision: Union[str, None] = '9bfdb9479391'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add reason column to credit_movements (for sales credit notes)
    op.add_column('credit_movements', sa.Column('reason', sa.Text(), nullable=True))

    # Create purchase_credit_movements table
    op.create_table(
        'purchase_credit_movements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('purchase_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('movement_type', sa.String(length=60), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('date', sa.DateTime(), nullable=True),
        sa.Column('reference_purchase_number', sa.String(length=30), nullable=True),
        sa.Column('reference_control_number', sa.String(length=20), nullable=True),
        sa.Column('stock_reverted', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('warehouse_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['purchase_id'], ['purchases.id'], ),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop purchase_credit_movements table
    op.drop_table('purchase_credit_movements')

    # Remove reason column from credit_movements
    op.drop_column('credit_movements', 'reason')
