"""add_latitude_longitude_to_customers

Revision ID: 8951370b0191
Revises: 20260112000001
Create Date: 2026-01-14 09:58:38.678513

Agregar campos de ubicación geográfica (latitud y longitud) a la tabla customers
para permitir la visualización de clientes en un mapa.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8951370b0191'
down_revision: Union[str, None] = '20260112000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Obtener conexión para ejecutar SQL directo
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Verificar columnas existentes en customers
    customers_columns = [col['name'] for col in inspector.get_columns('customers')]

    # ================= CUSTOMERS =================
    # Agregar campos de ubicación geográfica solo si no existen
    if 'latitude' not in customers_columns:
        op.add_column('customers', sa.Column('latitude', sa.Float(), nullable=True))
    if 'longitude' not in customers_columns:
        op.add_column('customers', sa.Column('longitude', sa.Float(), nullable=True))


def downgrade() -> None:
    # Eliminar los campos de ubicación geográfica
    op.drop_column('customers', 'latitude')
    op.drop_column('customers', 'longitude')
