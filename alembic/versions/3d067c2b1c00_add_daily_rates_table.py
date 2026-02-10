"""add_daily_rates_table

Revision ID: 3d067c2b1c00
Revises: 20250117_add_igtf_purchases
Create Date: 2026-01-17 12:42:04.444082

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d067c2b1c00'
down_revision: Union[str, None] = '20250117_add_igtf_purchases'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Crear tabla daily_rates para historial completo de tasas de cambio.

    Esta tabla almacena el historial de tasas diarias de todas las monedas,
    permitiendo auditoría completa y trazabilidad de conversiones.
    """
    # Crear tabla daily_rates
    op.create_table(
        'daily_rates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('base_currency_id', sa.Integer(), nullable=False),
        sa.Column('target_currency_id', sa.Integer(), nullable=False),
        sa.Column('rate_date', sa.Date(), nullable=False),
        sa.Column('exchange_rate', sa.Float(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='MANUAL'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('meta_data', sa.String(length=1000), nullable=True),
        sa.ForeignKeyConstraint(['base_currency_id'], ['currencies.id'], name=op.f('fk_daily_rates_base_currency_id_currencies')),
        sa.ForeignKeyConstraint(['target_currency_id'], ['currencies.id'], name=op.f('fk_daily_rates_target_currency_id_currencies')),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_daily_rates_company_id_companies')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_daily_rates_created_by_users')),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name=op.f('fk_daily_rates_updated_by_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_daily_rates')),
        sa.UniqueConstraint('company_id', 'base_currency_id', 'target_currency_id', 'rate_date', name='uq_daily_rate_per_day')
    )

    # Crear índices para búsquedas eficientes
    op.create_index('idx_daily_rate_company_date', 'daily_rates', ['company_id', 'rate_date'])
    op.create_index('idx_daily_rate_currencies', 'daily_rates', ['base_currency_id', 'target_currency_id'])
    op.create_index('idx_daily_rate_date', 'daily_rates', ['rate_date'])
    op.create_index(op.f('ix_daily_rates_company_id'), 'daily_rates', ['company_id'])
    op.create_index(op.f('ix_daily_rates_base_currency_id'), 'daily_rates', ['base_currency_id'])
    op.create_index(op.f('ix_daily_rates_target_currency_id'), 'daily_rates', ['target_currency_id'])


def downgrade() -> None:
    """
    Eliminar tabla daily_rates y sus índices.
    """
    # Eliminar índices primero
    op.drop_index(op.f('ix_daily_rates_target_currency_id'), table_name='daily_rates')
    op.drop_index(op.f('ix_daily_rates_base_currency_id'), table_name='daily_rates')
    op.drop_index(op.f('ix_daily_rates_company_id'), table_name='daily_rates')
    op.drop_index('idx_daily_rate_date', table_name='daily_rates')
    op.drop_index('idx_daily_rate_currencies', table_name='daily_rates')
    op.drop_index('idx_daily_rate_company_date', table_name='daily_rates')

    # Eliminar tabla
    op.drop_table('daily_rates')
