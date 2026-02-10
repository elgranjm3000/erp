"""add_coin_history_table_desktop_erp

Revision ID: 7e3cbf82afb4
Revises: e07afe838b21
Create Date: 2026-01-18 22:10:06.231019

✅ SISTEMA ESCRITORIO: Agrega tabla coin_history basada en PostgreSQL
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e3cbf82afb4'
down_revision: Union[str, None] = 'e07afe838b21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==================== ✅ CREATE COIN_HISTORY TABLE ====================

    op.create_table(
        'coin_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('currency_id', sa.Integer(), nullable=False, comment='Referencia a la moneda (main_code en PostgreSQL)'),
        sa.Column('sales_aliquot', sa.Float(), nullable=False, comment='Tasa de venta (cuanto vale en moneda local)'),
        sa.Column('buy_aliquot', sa.Float(), nullable=False, comment='Tasa de compra'),
        sa.Column('register_date', sa.Date(), nullable=False, comment='Fecha del registro'),
        sa.Column('register_hour', sa.Time(), nullable=False, comment='Hora del registro'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='Usuario que registró el cambio'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name='fk_coin_history_company_id'),
        sa.ForeignKeyConstraint(['currency_id'], ['currencies.id'], name='fk_coin_history_currency_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_coin_history_user_id'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_coin_history_id', 'coin_history', ['id'], unique=True)
    op.create_index('ix_coin_history_company_id', 'coin_history', ['company_id'])
    op.create_index('ix_coin_history_currency_id', 'coin_history', ['currency_id'])
    op.create_index('ix_coin_history_register_date', 'coin_history', ['register_date'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_coin_history_register_date', table_name='coin_history')
    op.drop_index('ix_coin_history_currency_id', table_name='coin_history')
    op.drop_index('ix_coin_history_company_id', table_name='coin_history')
    op.drop_index('ix_coin_history_id', table_name='coin_history')

    # Drop table
    op.drop_table('coin_history')

