"""add chat read tracking

Revision ID: add_chat_read_tracking
Revises: f8b9c4d5e6a7
Create Date: 2024-04-14 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_chat_read_tracking'
down_revision = 'f8b9c4d5e6a7'
branch_labels = None
depends_on = None


def upgrade():
    # Create chat_thread_read_status table
    op.create_table('chat_thread_read_status',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('thread_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('last_read_message_id', sa.Integer(), nullable=True),
        sa.Column('last_read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('unread_count', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['thread_id'], ['chat_threads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['last_read_message_id'], ['chat_messages.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('thread_id', 'user_id', name='uq_thread_user_read_status')
    )
    op.create_index('idx_chat_read_status_thread', 'chat_thread_read_status', ['thread_id'])
    op.create_index('idx_chat_read_status_user', 'chat_thread_read_status', ['user_id'])
    
    # Add is_dm_notification column to chat_messages for marking DM messages
    op.add_column('chat_messages', sa.Column('is_dm_notification', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add mentioned_user_ids column to chat_messages for tracking mentions
    op.add_column('chat_messages', sa.Column('mentioned_user_ids', postgresql.ARRAY(sa.Integer()), nullable=True))
    op.create_index('idx_chat_msg_mentions', 'chat_messages', ['mentioned_user_ids'], postgresql_using='gin')


def downgrade():
    op.drop_index('idx_chat_msg_mentions', table_name='chat_messages')
    op.drop_column('chat_messages', 'mentioned_user_ids')
    op.drop_column('chat_messages', 'is_dm_notification')
    
    op.drop_index('idx_chat_read_status_user', table_name='chat_thread_read_status')
    op.drop_index('idx_chat_read_status_thread', table_name='chat_thread_read_status')
    op.drop_table('chat_thread_read_status')
