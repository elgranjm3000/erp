"""fix_user_agent_column_and_create_igtf_table

Revision ID: 0b4ff9112d8a
Revises: b7d48f3525eb
Create Date: 2026-01-16 18:54:27.540797

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b4ff9112d8a'
down_revision: Union[str, None] = 'b7d48f3525eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add user_agent column if it doesn't exist
    # Using op.execute with SQL to check if column exists first
    from sqlalchemy import text
    conn = op.get_bind()

    # Check if user_agent column exists in currency_rate_history
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('currency_rate_history')]

    if 'user_agent' not in columns:
        op.add_column('currency_rate_history',
                     sa.Column('user_agent', sa.String(500), nullable=True,
                              comment='User agent from HTTP request'))

    # 2. Create igtf_config table if it doesn't exist
    tables = inspector.get_table_names()
    if 'igtf_config' not in tables:
        op.create_table(
            'igtf_config',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('company_id', sa.Integer(), nullable=False),
            sa.Column('currency_id', sa.Integer(), nullable=False),
            sa.Column('is_special_contributor', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('igtf_rate', sa.Numeric(precision=5, scale=2), nullable=False),
            sa.Column('min_amount_local', sa.Numeric(precision=20, scale=2), nullable=True),
            sa.Column('min_amount_foreign', sa.Numeric(precision=20, scale=2), nullable=True),
            sa.Column('is_exempt', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('exempt_transactions', sa.Text(), nullable=True),
            sa.Column('applicable_payment_methods', sa.Text(), nullable=True),
            sa.Column('valid_from', sa.DateTime(), nullable=False),
            sa.Column('valid_until', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
            sa.ForeignKeyConstraint(['currency_id'], ['currencies.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('company_id', 'currency_id', name='uq_igtf_config_per_currency')
        )
        op.create_index('idx_igtf_company_active', 'igtf_config',
                       ['company_id', 'valid_from', 'valid_until'])


def downgrade() -> None:
    # Remove igtf_config table
    op.drop_index('idx_igtf_company_active', table_name='igtf_config')
    op.drop_table('igtf_config')

    # Remove user_agent column
    op.drop_column('currency_rate_history', 'user_agent')
