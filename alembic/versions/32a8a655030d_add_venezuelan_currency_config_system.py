"""add_venezuelan_currency_config_system

Revision ID: 32a8a655030d
Revises: b6f0b74a4cc3
Create Date: 2026-01-15 14:48:39.584596

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '32a8a655030d'
down_revision: Union[str, None] = 'b6f0b74a4cc3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==================== AGREGAR COLUMNAS FALTANTES A currencies ====================
    # Solo agregar columnas que no existen

    # IGTF
    try:
        op.add_column('currencies', sa.Column('applies_igtf', sa.Boolean(), nullable=True, server_default='0'))
    except:
        pass

    try:
        op.add_column('currencies', sa.Column('igtf_rate', sa.Numeric(precision=5, scale=2), nullable=True))
    except:
        pass

    try:
        op.add_column('currencies', sa.Column('igtf_exempt', sa.Boolean(), nullable=True, server_default='0'))
    except:
        pass

    try:
        op.add_column('currencies', sa.Column('igtf_min_amount', sa.Numeric(precision=20, scale=2), nullable=True))
    except:
        pass

    # Actualización automática
    try:
        op.add_column('currencies', sa.Column('rate_update_method', sa.String(20), nullable=True, server_default='manual'))
    except:
        pass

    try:
        op.add_column('currencies', sa.Column('last_rate_update', sa.DateTime(), nullable=True))
    except:
        pass

    try:
        op.add_column('currencies', sa.Column('next_rate_update', sa.DateTime(), nullable=True))
    except:
        pass

    try:
        op.add_column('currencies', sa.Column('rate_source_url', sa.String(500), nullable=True))
    except:
        pass

    # Usuario
    try:
        op.add_column('currencies', sa.Column('created_by', sa.Integer(), nullable=True))
    except:
        pass

    try:
        op.add_column('currencies', sa.Column('updated_by', sa.Integer(), nullable=True))
    except:
        pass

    # Notas
    try:
        op.add_column('currencies', sa.Column('notes', sa.Text(), nullable=True))
    except:
        pass

    try:
        op.add_column('currencies', sa.Column('config', sa.Text(), nullable=True))
    except:
        pass

    # Crear índices si no existen
    try:
        op.create_index('idx_currency_company_active', 'currencies', ['company_id', 'is_active'])
    except:
        pass

    try:
        op.create_index('idx_currency_igtf', 'currencies', ['company_id', 'applies_igtf', 'is_active'])
    except:
        pass

    try:
        op.create_index('idx_currency_base', 'currencies', ['company_id', 'is_base_currency'])
    except:
        pass

    # ==================== CREAR TABLA: currency_rate_history ====================
    try:
        op.create_table(
            'currency_rate_history',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('currency_id', sa.Integer(), nullable=False),
            sa.Column('company_id', sa.Integer(), nullable=False),

            # Cambios
            sa.Column('old_rate', sa.Numeric(precision=20, scale=10), nullable=False),
            sa.Column('new_rate', sa.Numeric(precision=20, scale=10), nullable=False),
            sa.Column('rate_difference', sa.Numeric(precision=20, scale=10), nullable=True),
            sa.Column('rate_variation_percent', sa.Numeric(precision=10, scale=4), nullable=True),

            # Metadata
            sa.Column('changed_by', sa.Integer(), nullable=True),
            sa.Column('change_type', sa.String(20), nullable=True),
            sa.Column('change_source', sa.String(100), nullable=True),
            sa.Column('user_ip', sa.String(45), nullable=True),
            sa.Column('changed_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
            sa.Column('change_reason', sa.Text(), nullable=True),
            sa.Column('provider_metadata', sa.Text(), nullable=True),

            sa.ForeignKeyConstraint(['currency_id'], ['currencies.id']),
            sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
            sa.PrimaryKeyConstraint('id')
        )

        # Índices para CurrencyRateHistory
        op.create_index('idx_rate_history_currency', 'currency_rate_history', ['currency_id', 'changed_at'])
        op.create_index('idx_rate_history_company', 'currency_rate_history', ['company_id', 'currency_id'])
    except:
        pass

    # ==================== CREAR TABLA: igtf_configs ====================
    try:
        op.create_table(
            'igtf_configs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('company_id', sa.Integer(), nullable=False),
            sa.Column('currency_id', sa.Integer(), nullable=False),

            # Contribuyente especial
            sa.Column('is_special_contributor', sa.Boolean(), nullable=True, server_default='0'),

            # Tasa
            sa.Column('igtf_rate', sa.Numeric(precision=5, scale=2), nullable=False),
            sa.Column('min_amount_local', sa.Numeric(precision=20, scale=2), nullable=True),
            sa.Column('min_amount_foreign', sa.Numeric(precision=20, scale=2), nullable=True),

            # Exenciones
            sa.Column('is_exempt', sa.Boolean(), nullable=True, server_default='0'),
            sa.Column('exempt_transactions', sa.Text(), nullable=True),
            sa.Column('applicable_payment_methods', sa.Text(), nullable=True),

            # Vigencia
            sa.Column('valid_from', sa.DateTime(), nullable=False),
            sa.Column('valid_until', sa.DateTime(), nullable=True),

            # Timestamps
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),

            sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
            sa.ForeignKeyConstraint(['currency_id'], ['currencies.id']),
            sa.PrimaryKeyConstraint('id')
        )

        # Índices para IGTFConfig
        op.create_index('idx_igtf_company_currency', 'igtf_configs', ['company_id', 'currency_id'])
        op.create_index('idx_igtf_validity', 'igtf_configs', ['valid_from', 'valid_until'])
    except:
        pass


def downgrade() -> None:
    # Drop en orden inverso (sin errores si no existen)
    try:
        op.drop_index('idx_igtf_validity', 'igtf_configs')
        op.drop_index('idx_igtf_company_currency', 'igtf_configs')
        op.drop_table('igtf_configs')
    except:
        pass

    try:
        op.drop_index('idx_rate_history_company', 'currency_rate_history')
        op.drop_index('idx_rate_history_currency', 'currency_rate_history')
        op.drop_table('currency_rate_history')
    except:
        pass

    # Quitar índices de currencies
    try:
        op.drop_index('idx_currency_base', 'currencies')
    except:
        pass

    try:
        op.drop_index('idx_currency_igtf', 'currencies')
    except:
        pass

    try:
        op.drop_index('idx_currency_company_active', 'currencies')
    except:
        pass

    # Quitar columnas agregadas
    try:
        op.drop_column('currencies', 'config')
    except:
        pass

    try:
        op.drop_column('currencies', 'notes')
    except:
        pass

    try:
        op.drop_column('currencies', 'updated_by')
    except:
        pass

    try:
        op.drop_column('currencies', 'created_by')
    except:
        pass

    try:
        op.drop_column('currencies', 'rate_source_url')
    except:
        pass

    try:
        op.drop_column('currencies', 'next_rate_update')
    except:
        pass

    try:
        op.drop_column('currencies', 'last_rate_update')
    except:
        pass

    try:
        op.drop_column('currencies', 'rate_update_method')
    except:
        pass

    try:
        op.drop_column('currencies', 'igtf_min_amount')
    except:
        pass

    try:
        op.drop_column('currencies', 'igtf_exempt')
    except:
        pass

    try:
        op.drop_column('currencies', 'igtf_rate')
    except:
        pass

    try:
        op.drop_column('currencies', 'applies_igtf')
    except:
        pass
