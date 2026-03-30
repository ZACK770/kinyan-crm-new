"""global_table_prefs storage_key unique

Revision ID: 925a8ee3a9f0
Revises: b3df86a076ee
Create Date: 2026-03-30 13:47:30.136530
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '925a8ee3a9f0'
down_revision: Union[str, None] = 'b3df86a076ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
