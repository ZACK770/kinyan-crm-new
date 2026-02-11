"""enhance leads collections nedarim integration

Revision ID: d9f8e7c6b5a4
Revises: c8f5a2b3d4e6
Create Date: 2026-02-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9f8e7c6b5a4'
down_revision: Union[str, None] = 'c8f5a2b3d4e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ═══════════════════════════════════════════════════════════════
    # LEADS TABLE - Add payment tracking fields
    # ═══════════════════════════════════════════════════════════════
    
    # Add selected_product_id (FK to lead_products)
    op.add_column('leads', sa.Column('selected_product_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_leads_selected_product',
        'leads', 'lead_products',
        ['selected_product_id'], ['id'],
        use_alter=True
    )
    
    # Add first_payment_id (FK to payments)
    op.add_column('leads', sa.Column('first_payment_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_leads_first_payment',
        'leads', 'payments',
        ['first_payment_id'], ['id'],
        use_alter=True
    )
    
    # Add nedarim_payment_link
    op.add_column('leads', sa.Column('nedarim_payment_link', sa.String(500), nullable=True))
    
    # ═══════════════════════════════════════════════════════════════
    # COLLECTIONS TABLE - Enhanced schema with Nedarim integration
    # ═══════════════════════════════════════════════════════════════
    
    # Add payment_id (FK to payments)
    op.add_column('collections', sa.Column('payment_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_collections_payment',
        'collections', 'payments',
        ['payment_id'], ['id']
    )
    
    # Add course_id (FK to courses)
    op.add_column('collections', sa.Column('course_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_collections_course',
        'collections', 'courses',
        ['course_id'], ['id']
    )
    
    # Add installment tracking fields
    op.add_column('collections', sa.Column('charge_day', sa.Integer(), nullable=True))
    op.add_column('collections', sa.Column('installment_number', sa.Integer(), nullable=True))
    op.add_column('collections', sa.Column('total_installments', sa.Integer(), nullable=True))
    
    # Add Nedarim Plus integration fields
    op.add_column('collections', sa.Column('nedarim_donation_id', sa.String(50), nullable=True))
    op.add_column('collections', sa.Column('nedarim_transaction_id', sa.String(50), nullable=True))
    op.add_column('collections', sa.Column('nedarim_subscription_id', sa.String(50), nullable=True))
    
    # Create new indexes for collections
    op.create_index('idx_collections_nedarim', 'collections', ['nedarim_donation_id'])
    op.create_index('idx_collections_commitment', 'collections', ['commitment_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_collections_commitment', table_name='collections')
    op.drop_index('idx_collections_nedarim', table_name='collections')
    
    # Remove Nedarim fields from collections
    op.drop_column('collections', 'nedarim_subscription_id')
    op.drop_column('collections', 'nedarim_transaction_id')
    op.drop_column('collections', 'nedarim_donation_id')
    
    # Remove installment tracking fields
    op.drop_column('collections', 'total_installments')
    op.drop_column('collections', 'installment_number')
    op.drop_column('collections', 'charge_day')
    
    # Remove course FK
    op.drop_constraint('fk_collections_course', 'collections', type_='foreignkey')
    op.drop_column('collections', 'course_id')
    
    # Remove payment FK
    op.drop_constraint('fk_collections_payment', 'collections', type_='foreignkey')
    op.drop_column('collections', 'payment_id')
    
    # Remove leads fields
    op.drop_column('leads', 'nedarim_payment_link')
    
    op.drop_constraint('fk_leads_first_payment', 'leads', type_='foreignkey')
    op.drop_column('leads', 'first_payment_id')
    
    op.drop_constraint('fk_leads_selected_product', 'leads', type_='foreignkey')
    op.drop_column('leads', 'selected_product_id')
