"""add global_table_prefs

Revision ID: e0881dacc6bb
Revises: 5eeaae9f7aaa
Create Date: 2026-03-23 13:48:43.726840
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = 'e0881dacc6bb'
down_revision: Union[str, None] = '5eeaae9f7aaa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS global_table_prefs (
            id SERIAL PRIMARY KEY,
            storage_key VARCHAR(200) NOT NULL UNIQUE,
            data JSON,
            updated_by_user_id INTEGER REFERENCES users (id) ON DELETE SET NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_global_table_prefs_storage_key
        ON global_table_prefs (storage_key);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS idx_global_table_prefs_storage_key;
        """
    )
    op.execute(
        """
        DROP TABLE IF EXISTS global_table_prefs;
        """
    )
