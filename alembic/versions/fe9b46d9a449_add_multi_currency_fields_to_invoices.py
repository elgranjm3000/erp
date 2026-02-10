"""add_multi_currency_fields_to_invoices

Revision ID: fe9b46d9a449
Revises: 3d067c2b1c00
Create Date: 2026-01-17 12:49:12.248273

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe9b46d9a449'
down_revision: Union[str, None] = '3d067c2b1c00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Agregar campos multi-moneda a la tabla invoices.

    Campos agregados:
    - reference_currency_id: Moneda de referencia (USD) para precios de productos
    - manual_exchange_rate: Tasa manual para override (permite usar tasa diferente a BCV)
    """
    # Agregar reference_currency_id (FK a currencies)
    op.add_column(
        'invoices',
        sa.Column('reference_currency_id', sa.Integer(), nullable=True)
    )

    # Crear FK para reference_currency_id
    op.create_foreign_key(
        'fk_invoices_reference_currency_id_currencies',
        'invoices', 'currencies',
        ['reference_currency_id'], ['id']
    )

    # Crear índice para reference_currency_id
    op.create_index(
        'ix_invoices_reference_currency_id',
        'invoices',
        ['reference_currency_id']
    )

    # Agregar manual_exchange_rate (para override de tasa BCV)
    op.add_column(
        'invoices',
        sa.Column('manual_exchange_rate', sa.Float(), nullable=True)
    )


def downgrade() -> None:
    """
    Eliminar campos multi-moneda de la tabla invoices.
    """
    # Eliminar manual_exchange_rate
    op.drop_column('invoices', 'manual_exchange_rate')

    # Eliminar índice y FK de reference_currency_id
    op.drop_index('ix_invoices_reference_currency_id', table_name='invoices')
    op.drop_constraint('fk_invoices_reference_currency_id_currencies', 'invoices', type_='foreignkey')

    # Eliminar reference_currency_id
    op.drop_column('invoices', 'reference_currency_id')
