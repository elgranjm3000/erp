"""add product price history

Revision ID: add_product_price_history
Revises: add_igtf_to_invoices
Create Date: 2026-01-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_product_price_history'
down_revision = 'add_igtf_to_invoices'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'product_price_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('currency_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('old_price', sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column('new_price', sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column('price_difference', sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column('price_variation_percent', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('changed_by', sa.Integer(), nullable=True),
        sa.Column('change_type', sa.String(length=20), nullable=False),
        sa.Column('change_source', sa.String(length=100), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('change_metadata', sa.Text(), nullable=True),
        sa.Column('changed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['currency_id'], ['currencies.id'], ),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_product_price_history_product_id', 'product_price_history', ['product_id'])
    op.create_index('ix_product_price_history_currency_id', 'product_price_history', ['currency_id'])
    op.create_index('ix_product_price_history_company_id', 'product_price_history', ['company_id'])
    op.create_index('ix_product_price_history_changed_at', 'product_price_history', ['changed_at'])


def downgrade():
    op.drop_index('ix_product_price_history_changed_at', table_name='product_price_history')
    op.drop_index('ix_product_price_history_company_id', table_name='product_price_history')
    op.drop_index('ix_product_price_history_currency_id', table_name='product_price_history')
    op.drop_index('ix_product_price_history_product_id', table_name='product_price_history')
    op.drop_table('product_price_history')
