"""merge heads

Revision ID: bb7cd3612765
Revises: b7c2d841f0a3, nedarim_plus_integration
Create Date: 2026-02-10 18:37:36.478477
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = 'bb7cd3612765'
down_revision: Union[str, None] = ('b7c2d841f0a3', 'nedarim_plus_integration')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
