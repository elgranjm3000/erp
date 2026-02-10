"""add_ref_fields_to_invoices

Revision ID: bc5d19d3f4c7
Revises: 69702ff4b37a
Create Date: 2026-01-17 18:55:04.316735

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc5d19d3f4c7'
down_revision: Union[str, None] = '69702ff4b37a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add REF fields to invoices table
    op.add_column('invoices', sa.Column('subtotal_reference', sa.Float(), nullable=True))
    op.add_column('invoices', sa.Column('subtotal_target', sa.Float(), nullable=True))


def downgrade() -> None:
    # Remove REF fields from invoices table
    op.drop_column('invoices', 'subtotal_target')
    op.drop_column('invoices', 'subtotal_reference')
