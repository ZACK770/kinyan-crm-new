"""Add files table for R2 storage tracking

Revision ID: c8f5a2b3d4e6
Revises: aeab5716f39e
Create Date: 2026-02-10 20:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = 'c8f5a2b3d4e6'
down_revision: Union[str, None] = 'aeab5716f39e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'files' not in inspector.get_table_names():
        op.create_table('files',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('filename', sa.String(length=500), nullable=False),
            sa.Column('storage_key', sa.String(length=500), nullable=False),
            sa.Column('content_type', sa.String(length=100), nullable=True),
            sa.Column('size_bytes', sa.Integer(), nullable=True),
            sa.Column('entity_type', sa.String(length=100), nullable=True),
            sa.Column('entity_id', sa.Integer(), nullable=True),
            sa.Column('uploaded_by', sa.Integer(), nullable=True),
            sa.Column('description', sa.String(length=500), nullable=True),
            sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('storage_key')
        )
        op.create_index('idx_files_entity', 'files', ['entity_type', 'entity_id'], unique=False)
        op.create_index('idx_files_storage_key', 'files', ['storage_key'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_files_storage_key', table_name='files')
    op.drop_index('idx_files_entity', table_name='files')
    op.drop_table('files')
