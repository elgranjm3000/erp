"""add_warehouse_id_to_products

Revision ID: 6d95890ea918
Revises: b094b158605f
Create Date: 2026-01-20 00:39:50.642417

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6d95890ea918'
down_revision: Union[str, None] = 'b094b158605f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar columna warehouse_id a la tabla products
    op.add_column('products', sa.Column('warehouse_id', sa.Integer(), nullable=True))
    # Crear foreign key constraint
    op.create_foreign_key(
        'fk_products_warehouse_id', 'products', 'warehouses',
        ['warehouse_id'], ['id']
    )


def downgrade() -> None:
    # Eliminar foreign key y columna
    op.drop_constraint('fk_products_warehouse_id', 'products', type_='foreignkey')
    op.drop_column('products', 'warehouse_id')
