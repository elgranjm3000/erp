"""add igtf columns to purchases

Revision ID: 20250117_add_igtf_purchases
Revises: 20250117_add_igtf
Create Date: 2026-01-17 11:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250117_add_igtf_purchases'
down_revision: Union[str, None] = '20250117_add_igtf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add IGTF columns to purchases table
    op.add_column('purchases',
                  sa.Column('igtf_amount', sa.Float(), nullable=True, server_default='0')
                  )
    op.add_column('purchases',
                  sa.Column('igtf_percentage', sa.Float(), nullable=True, server_default='0')
                  )
    op.add_column('purchases',
                  sa.Column('igtf_exempt', sa.Boolean(), nullable=True, server_default='0')
                  )


def downgrade() -> None:
    # Remove IGTF columns from purchases table
    op.drop_column('purchases', 'igtf_exempt')
    op.drop_column('purchases', 'igtf_percentage')
    op.drop_column('purchases', 'igtf_amount')
