"""merge all branches

Revision ID: 5f5717122e85
Revises: add_chat_message_read_receipts, add_send_reminder_to_sales_tasks, 840f7bd52ad2
Create Date: 2026-04-22 14:55:35.944536
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '5f5717122e85'
down_revision: Union[str, None] = ('add_chat_message_read_receipts', 'add_send_reminder_to_sales_tasks', '840f7bd52ad2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
