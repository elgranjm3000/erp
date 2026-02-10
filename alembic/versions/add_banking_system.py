"""add banking system

Revision ID: add_banking_system
Revises: add_product_price_history
Create Date: 2026-01-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_banking_system'
down_revision = 'add_product_price_history'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'bank_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('currency_id', sa.Integer(), nullable=False),
        sa.Column('account_number', sa.String(length=50), nullable=False),
        sa.Column('account_type', sa.String(length=20), nullable=False, server_default='corriente'),
        sa.Column('bank_name', sa.String(length=100), nullable=False),
        sa.Column('bank_code', sa.String(length=20), nullable=True),
        sa.Column('balance', sa.Numeric(precision=20, scale=2), nullable=False, server_default='0.00'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('balance_last_updated', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['currency_id'], ['currencies.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_bank_accounts_id', 'bank_accounts', ['id'])
    op.create_index('ix_bank_accounts_company_id', 'bank_accounts', ['company_id'])
    op.create_index('ix_bank_accounts_currency_id', 'bank_accounts', ['currency_id'])
    op.create_index('ix_bank_accounts_account_number', 'bank_accounts', ['account_number'])
    op.create_index('idx_bank_account_company_currency', 'bank_accounts', ['company_id', 'currency_id'])
    op.create_index('idx_bank_account_active', 'bank_accounts', ['company_id', 'is_active'])

    op.create_table(
        'bank_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('bank_account_id', sa.Integer(), nullable=False),
        sa.Column('currency_id', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column('exchange_rate', sa.Numeric(precision=20, scale=10), nullable=True),
        sa.Column('exchange_rate_date', sa.DateTime(), nullable=True),
        sa.Column('base_currency_amount', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('reference_number', sa.String(length=100), nullable=True),
        sa.Column('transaction_date', sa.DateTime(), nullable=False),
        sa.Column('related_invoice_id', sa.Integer(), nullable=True),
        sa.Column('related_purchase_id', sa.Integer(), nullable=True),
        sa.Column('is_reconciled', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('reconciliation_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('recorded_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['bank_account_id'], ['bank_accounts.id'], ),
        sa.ForeignKeyConstraint(['currency_id'], ['currencies.id'], ),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['related_invoice_id'], ['invoices.id'], ),
        sa.ForeignKeyConstraint(['related_purchase_id'], ['purchases.id'], ),
        sa.ForeignKeyConstraint(['recorded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_bank_transactions_id', 'bank_transactions', ['id'])
    op.create_index('ix_bank_transactions_company_id', 'bank_transactions', ['company_id'])
    op.create_index('ix_bank_transactions_bank_account_id', 'bank_transactions', ['bank_account_id'])
    op.create_index('ix_bank_transactions_currency_id', 'bank_transactions', ['currency_id'])
    op.create_index('ix_bank_transactions_transaction_type', 'bank_transactions', ['transaction_type'])
    op.create_index('ix_bank_transactions_reference_number', 'bank_transactions', ['reference_number'])
    op.create_index('ix_bank_transactions_transaction_date', 'bank_transactions', ['transaction_date'])
    op.create_index('ix_bank_transactions_related_invoice_id', 'bank_transactions', ['related_invoice_id'])
    op.create_index('ix_bank_transactions_related_purchase_id', 'bank_transactions', ['related_purchase_id'])
    op.create_index('ix_bank_transactions_is_reconciled', 'bank_transactions', ['is_reconciled'])
    op.create_index('idx_bank_transaction_account_date', 'bank_transactions', ['bank_account_id', 'transaction_date'])
    op.create_index('idx_bank_transaction_reconciled', 'bank_transactions', ['company_id', 'is_reconciled'])


def downgrade():
    op.drop_index('idx_bank_transaction_reconciled', table_name='bank_transactions')
    op.drop_index('idx_bank_transaction_account_date', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_is_reconciled', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_related_purchase_id', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_related_invoice_id', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_transaction_date', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_reference_number', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_transaction_type', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_currency_id', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_bank_account_id', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_company_id', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_id', table_name='bank_transactions')
    op.drop_table('bank_transactions')

    op.drop_index('idx_bank_account_active', table_name='bank_accounts')
    op.drop_index('idx_bank_account_company_currency', table_name='bank_accounts')
    op.drop_index('ix_bank_accounts_account_number', table_name='bank_accounts')
    op.drop_index('ix_bank_accounts_currency_id', table_name='bank_accounts')
    op.drop_index('ix_bank_accounts_company_id', table_name='bank_accounts')
    op.drop_index('ix_bank_accounts_id', table_name='bank_accounts')
    op.drop_table('bank_accounts')
