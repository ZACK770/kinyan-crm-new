"""Add Nedarim Plus integration fields

Revision ID: nedarim_plus_integration
Revises: aeab5716f39e
Create Date: 2026-02-10

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'nedarim_plus_integration'
down_revision: Union[str, None] = 'aeab5716f39e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Check students table columns
    student_columns = [c['name'] for c in inspector.get_columns('students')]
    
    if 'nedarim_id' in student_columns and 'nedarim_payer_id' not in student_columns:
        # Rename nedarim_id to nedarim_payer_id in students table
        op.alter_column('students', 'nedarim_id', new_column_name='nedarim_payer_id')
    elif 'nedarim_payer_id' not in student_columns:
        # If neither exists (shouldn't happen based on model, but safe fallback)
        op.add_column('students', sa.Column('nedarim_payer_id', sa.String(50), nullable=True))

    # Check payments table columns
    payment_columns = [c['name'] for c in inspector.get_columns('payments')]
    
    if 'nedarim_donation_id' not in payment_columns:
        op.add_column('payments', sa.Column('nedarim_donation_id', sa.String(50), nullable=True))
        op.create_index('idx_payments_nedarim', 'payments', ['nedarim_donation_id'])
        
    if 'nedarim_transaction_id' not in payment_columns:
        op.add_column('payments', sa.Column('nedarim_transaction_id', sa.String(50), nullable=True))
    
    # Check commitments table columns
    commitment_columns = [c['name'] for c in inspector.get_columns('commitments')]
    
    if 'nedarim_subscription_id' not in commitment_columns:
        op.add_column('commitments', sa.Column('nedarim_subscription_id', sa.String(50), nullable=True))
        op.create_index('idx_commitments_nedarim', 'commitments', ['nedarim_subscription_id'])


def downgrade() -> None:
    # Remove Nedarim field from commitments
    op.drop_index('idx_commitments_nedarim', table_name='commitments')
    op.drop_column('commitments', 'nedarim_subscription_id')
    
    # Remove Nedarim fields from payments
    op.drop_index('idx_payments_nedarim', table_name='payments')
    op.drop_column('payments', 'nedarim_transaction_id')
    op.drop_column('payments', 'nedarim_donation_id')
    
    # Rename back to nedarim_id
    op.alter_column('students', 'nedarim_payer_id', new_column_name='nedarim_id')
