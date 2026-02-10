"""add_invoice_rate_history

Revision ID: 3e9088ceb74b
Revises: bc5d19d3f4c7
Create Date: 2026-01-17 19:00:13.962282

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e9088ceb74b'
down_revision: Union[str, None] = 'bc5d19d3f4c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create invoice_rate_history table
    op.create_table(
        'invoice_rate_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('from_currency_id', sa.Integer(), nullable=False),
        sa.Column('to_currency_id', sa.Integer(), nullable=False),
        sa.Column('exchange_rate', sa.Float(), nullable=False),
        sa.Column('rate_source', sa.String(length=50), nullable=True),
        sa.Column('rate_date', sa.DateTime(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.ForeignKeyConstraint(['from_currency_id'], ['currencies.id']),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id']),
        sa.ForeignKeyConstraint(['to_currency_id'], ['currencies.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_rate_history_id'), 'invoice_rate_history', ['id'])


def downgrade() -> None:
    # Drop invoice_rate_history table
    op.drop_index(op.f('ix_invoice_rate_history_id'), table_name='invoice_rate_history')
    op.drop_table('invoice_rate_history')
