"""add_cost_to_products

Revision ID: caa9e2cefd34
Revises: 055c4924aac6
Create Date: 2026-01-17 19:51:16.645831

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'caa9e2cefd34'
down_revision: Union[str, None] = '055c4924aac6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add cost column to products
    op.add_column('products', sa.Column('cost', sa.Numeric(10, 2), nullable=True))


def downgrade() -> None:
    # Remove cost column from products
    op.drop_column('products', 'cost')
