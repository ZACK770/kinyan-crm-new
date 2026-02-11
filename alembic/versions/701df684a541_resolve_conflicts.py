"""resolve conflicts

Revision ID: 701df684a541
Revises: bb7cd3612765, d9f8e7c6b5a4, e1f2g3h4i5j6
Create Date: 2026-02-10 21:54:42.273144
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '701df684a541'
down_revision: Union[str, None] = ('bb7cd3612765', 'd9f8e7c6b5a4', 'e1f2g3h4i5j6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
