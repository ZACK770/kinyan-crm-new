"""merge_all_heads

Revision ID: 8877c651d63f
Revises: 23a7d5d4da0a, f1a2b3c4d5e6
Create Date: 2026-02-10 23:35:05.890448
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '8877c651d63f'
down_revision: Union[str, None] = ('23a7d5d4da0a', 'f1a2b3c4d5e6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
