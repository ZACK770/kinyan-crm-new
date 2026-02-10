"""update expenses schema - make description required, vendor optional, add category and notes

Revision ID: e1f2g3h4i5j6
Revises: c8f5a2b3d4e6
Create Date: 2026-02-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1f2g3h4i5j6'
down_revision = 'c8f5a2b3d4e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns
    op.add_column('expenses', sa.Column('category', sa.String(100), nullable=True))
    op.add_column('expenses', sa.Column('notes', sa.Text(), nullable=True))
    
    # Make vendor nullable (was NOT NULL)
    op.alter_column('expenses', 'vendor',
                    existing_type=sa.String(300),
                    nullable=True)
    
    # Make expense_date nullable
    op.alter_column('expenses', 'expense_date',
                    existing_type=sa.Date(),
                    nullable=True)
    
    # Change description from Text to String(500) and ensure it's usable
    # First, update any NULL descriptions to a default value
    op.execute("UPDATE expenses SET description = vendor WHERE description IS NULL")
    op.execute("UPDATE expenses SET description = 'הוצאה' WHERE description IS NULL OR description = ''")
    
    # Change column type and make non-nullable
    op.alter_column('expenses', 'description',
                    existing_type=sa.Text(),
                    type_=sa.String(500),
                    nullable=False)


def downgrade() -> None:
    # Revert description changes
    op.alter_column('expenses', 'description',
                    existing_type=sa.String(500),
                    type_=sa.Text(),
                    nullable=True)
    
    # Make vendor not nullable again
    op.execute("UPDATE expenses SET vendor = description WHERE vendor IS NULL")
    op.alter_column('expenses', 'vendor',
                    existing_type=sa.String(300),
                    nullable=False)
    
    # Make expense_date not nullable
    op.execute("UPDATE expenses SET expense_date = CURRENT_DATE WHERE expense_date IS NULL")
    op.alter_column('expenses', 'expense_date',
                    existing_type=sa.Date(),
                    nullable=False)
    
    # Drop new columns
    op.drop_column('expenses', 'notes')
    op.drop_column('expenses', 'category')
