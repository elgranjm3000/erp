"""add igtf_exempt to invoices

Revision ID: 20250117_add_igtf
Revises: add_banking_system
Create Date: 2026-01-17 11:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250117_add_igtf'
down_revision: Union[str, None] = 'add_banking_system'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add igtf_exempt column to invoices table
    op.add_column('invoices',
                  sa.Column('igtf_exempt', sa.Boolean(), nullable=True, server_default='0')
                  )


def downgrade() -> None:
    # Remove igtf_exempt column from invoices table
    op.drop_column('invoices', 'igtf_exempt')
