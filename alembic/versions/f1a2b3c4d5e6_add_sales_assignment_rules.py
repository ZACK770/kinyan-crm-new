"""add_sales_assignment_rules

Revision ID: f1a2b3c4d5e6
Revises: 611befc42c3c
Create Date: 2026-02-10 23:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = '611befc42c3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create sales_assignment_rules table
    op.create_table(
        'sales_assignment_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('salesperson_id', sa.Integer(), nullable=False),
        sa.Column('daily_lead_limit', sa.Integer(), nullable=True),
        sa.Column('daily_leads_assigned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_reset_date', sa.Date(), nullable=True),
        sa.Column('priority_weight', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('max_open_leads', sa.Integer(), nullable=True),
        sa.Column('status_filters', postgresql.ARRAY(sa.String()), nullable=True, server_default="ARRAY['ליד חדש', 'במעקב', 'מתעניין']"),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['salesperson_id'], ['salespeople.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('salesperson_id')
    )
    
    # Create indexes
    op.create_index('idx_assignment_rules_salesperson', 'sales_assignment_rules', ['salesperson_id'], unique=False)
    op.create_index('idx_assignment_rules_active', 'sales_assignment_rules', ['is_active'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_assignment_rules_active', table_name='sales_assignment_rules')
    op.drop_index('idx_assignment_rules_salesperson', table_name='sales_assignment_rules')
    
    # Drop table
    op.drop_table('sales_assignment_rules')
