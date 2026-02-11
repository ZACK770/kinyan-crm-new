"""merge_heads_for_nedarim

Revision ID: 6d51a6714aac
Revises: 701df684a541
Create Date: 2026-02-10 21:55:12.063246
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '6d51a6714aac'
down_revision: Union[str, None] = '701df684a541'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
