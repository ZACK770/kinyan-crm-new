"""add saved_filters to users

Revision ID: 5eeaae9f7aaa
Revises: fabf98f7e965
Create Date: 2026-03-23 13:32:33.921109
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '5eeaae9f7aaa'
down_revision: Union[str, None] = 'fabf98f7e965'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('saved_filters', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'saved_filters')
