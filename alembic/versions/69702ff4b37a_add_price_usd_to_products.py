"""add_price_usd_to_products

Revision ID: 69702ff4b37a
Revises: fe9b46d9a449
Create Date: 2026-01-17 12:49:52.136818

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69702ff4b37a'
down_revision: Union[str, None] = 'fe9b46d9a449'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Agregar campo price_usd a la tabla products.

    Este campo almacenará el precio referencial en USD (dólares americanos)
    para el sistema multi-moneda venezolano.

    El precio en USD es la moneda de referencia para todos los productos.
    Las facturas se generarán en VES usando la tasa BCV del día.
    """
    # Agregar price_usd como DECIMAL(10,2) para precios en USD
    op.add_column(
        'products',
        sa.Column('price_usd', sa.Numeric(precision=10, scale=2), nullable=True)
    )

    # Crear índice para price_usd (para búsquedas y filtros)
    op.create_index(
        'ix_products_price_usd',
        'products',
        ['price_usd']
    )


def downgrade() -> None:
    """
    Eliminar el campo price_usd de la tabla products.
    """
    # Eliminar índice
    op.drop_index('ix_products_price_usd', table_name='products')

    # Eliminar columna
    op.drop_column('products', 'price_usd')
