"""add igtf to invoices

Revision ID: add_igtf_to_invoices
Revises: 0b4ff9112d8a
Create Date: 2026-01-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_igtf_to_invoices'
down_revision = '0b4ff9112d8a'
branch_labels = None
depends_on = None


def upgrade():
    # Agregar campos IGTF a invoices
    op.add_column('invoices', sa.Column('igtf_amount', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('invoices', sa.Column('igtf_percentage', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('invoices', sa.Column('igtf_exempt', sa.Boolean(), nullable=True, server_default='0'))

    # Hacer lo mismo para purchases
    op.add_column('purchases', sa.Column('igtf_amount', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('purchases', sa.Column('igtf_percentage', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('purchases', sa.Column('igtf_exempt', sa.Boolean(), nullable=True, server_default='0'))


def downgrade():
    op.drop_column('purchases', 'igtf_exempt')
    op.drop_column('purchases', 'igtf_percentage')
    op.drop_column('purchases', 'igtf_amount')

    op.drop_column('invoices', 'igtf_exempt')
    op.drop_column('invoices', 'igtf_percentage')
    op.drop_column('invoices', 'igtf_amount')
