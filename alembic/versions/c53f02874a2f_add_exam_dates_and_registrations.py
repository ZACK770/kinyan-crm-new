"""Add exam dates and registrations

Revision ID: c53f02874a2f
Revises: b67e5a7290e1
Create Date: 2026-03-30 14:16:27.630882
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = 'c53f02874a2f'
down_revision: Union[str, None] = 'b67e5a7290e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Empty migration - all changes are in b67e5a7290e1
    pass


def downgrade() -> None:
    # Empty migration - all changes are in b67e5a7290e1
    pass
