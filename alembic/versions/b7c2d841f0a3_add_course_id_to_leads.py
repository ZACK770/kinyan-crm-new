"""add course_id to leads

Revision ID: b7c2d841f0a3
Revises: aeab5716f39e
Create Date: 2026-02-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c2d841f0a3'
down_revision: Union[str, None] = 'aeab5716f39e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add course_id column to leads table
    op.add_column('leads', sa.Column('course_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_leads_course_id', 
        'leads', 
        'courses', 
        ['course_id'], 
        ['id'],
        ondelete='SET NULL'
    )
    op.create_index('idx_leads_course', 'leads', ['course_id'])


def downgrade() -> None:
    op.drop_index('idx_leads_course', table_name='leads')
    op.drop_constraint('fk_leads_course_id', 'leads', type_='foreignkey')
    op.drop_column('leads', 'course_id')
