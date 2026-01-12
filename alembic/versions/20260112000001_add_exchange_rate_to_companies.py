"""add_exchange_rate_to_companies

Revision ID: 20260112000001
Revises: 7f9e1a3992d4
Create Date: 2026-01-12 00:00:01.000000

Agregar campos para cumplimiento SENIAT:
- Tasa de cambio USD->VES para cálculos correctos de retenciones (umbrales en Bolívares)
- Umbral para requerir RIF del cliente según monto de factura
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260112000001'
down_revision: Union[str, None] = '7f9e1a3992d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Obtener conexión para ejecutar SQL directo
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Verificar columnas existentes
    companies_columns = [col['name'] for col in inspector.get_columns('companies')]

    # ================= COMPANIES =================
    # Agregar campo de tasa de cambio solo si no existe
    if 'exchange_rate' not in companies_columns:
        op.add_column('companies', sa.Column('exchange_rate', sa.Float(), nullable=True, server_default='1.0'))

    # Agregar campo de umbral para RIF de cliente
    if 'require_customer_tax_id_threshold' not in companies_columns:
        op.add_column('companies', sa.Column('require_customer_tax_id_threshold', sa.Float(), nullable=True, server_default='0.0'))


def downgrade() -> None:
    # ================= COMPANIES =================
    op.drop_column('companies', 'require_customer_tax_id_threshold')
    op.drop_column('companies', 'exchange_rate')
