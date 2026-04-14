"""add personal course update fields to lead

Revision ID: 840f7bd52ad2
Revises: 3110d53c1eee
Create Date: 2026-04-14 13:58:30.345300
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = '840f7bd52ad2'
down_revision: Union[str, None] = '3110d53c1eee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add personal course update fields to leads table
    op.add_column('leads', sa.Column('personal_course_update', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('leads', sa.Column('personal_course_update_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('leads', sa.Column('personal_course_update_notes', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove personal course update fields from leads table
    op.drop_column('leads', 'personal_course_update_notes')
    op.drop_column('leads', 'personal_course_update_date')
    op.drop_column('leads', 'personal_course_update')
