"""add_product_price_history

Revision ID: 055c4924aac6
Revises: 3e9088ceb74b
Create Date: 2026-01-17 19:02:17.405177

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '055c4924aac6'
down_revision: Union[str, None] = '3e9088ceb74b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create product_price_history table
    op.create_table(
        'product_price_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('price_usd_old', sa.Numeric(10, 2), nullable=True),
        sa.Column('price_usd_new', sa.Numeric(10, 2), nullable=False),
        sa.Column('changed_at', sa.DateTime(), nullable=True),
        sa.Column('changed_by', sa.Integer(), nullable=True),
        sa.Column('change_reason', sa.String(length=200), nullable=True),
        sa.Column('change_source', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id']),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_product_price_history_id'), 'product_price_history', ['id'])


def downgrade() -> None:
    # Drop product_price_history table
    op.drop_index(op.f('ix_product_price_history_id'), table_name='product_price_history')
    op.drop_table('product_price_history')
