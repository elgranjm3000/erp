"""add_user_agent_to_currency_rate_history

Revision ID: b7d48f3525eb
Revises: 32a8a655030d
Create Date: 2026-01-16 18:41:26.684781

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7d48f3525eb'
down_revision: Union[str, None] = '32a8a655030d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user_agent column to currency_rate_history table
    op.add_column('currency_rate_history',
                  sa.Column('user_agent', sa.String(500), nullable=True))


def downgrade() -> None:
    # Remove user_agent column from currency_rate_history table
    op.drop_column('currency_rate_history', 'user_agent')
