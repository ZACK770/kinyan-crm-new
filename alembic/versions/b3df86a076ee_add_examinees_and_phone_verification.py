"""add examinees and phone verification

Revision ID: b3df86a076ee
Revises: e0881dacc6bb
Create Date: 2026-03-30 13:34:49.832632
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = 'b3df86a076ee'
down_revision: Union[str, None] = 'e0881dacc6bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # NOTE:
    # The initial autogenerate output included destructive operations
    # (dropping unrelated tables). This migration is intentionally limited
    # to the examinees + phone verification feature only.

    # --- phone_verification_challenges ---
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS phone_verification_challenges (
            id VARCHAR(36) PRIMARY KEY,
            phone VARCHAR(50) NOT NULL,
            verify_code_hash BYTEA NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            used_at TIMESTAMPTZ NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            provider VARCHAR(50) NOT NULL DEFAULT 'yemot',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_phone_verify_phone ON phone_verification_challenges (phone);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_phone_verify_expires ON phone_verification_challenges (expires_at);")

    # --- examinees ---
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS examinees (
            id SERIAL PRIMARY KEY,
            full_name VARCHAR(300) NULL,
            phone VARCHAR(50) NOT NULL,
            id_number VARCHAR(20) NULL,
            email VARCHAR(200) NULL,
            source VARCHAR(100) NOT NULL DEFAULT 'external_exam_product',
            student_id INTEGER NULL REFERENCES students(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_examinees_phone ON examinees (phone);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_examinees_student ON examinees (student_id);")

    # --- exam_submissions ---
    op.execute("ALTER TABLE exam_submissions ADD COLUMN IF NOT EXISTS examinee_id INTEGER NULL;")
    op.execute("ALTER TABLE exam_submissions ALTER COLUMN student_id DROP NOT NULL;")
    op.execute("CREATE INDEX IF NOT EXISTS idx_exam_sub_examinee ON exam_submissions (examinee_id);")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_exam_submissions_examinee_id'
            ) THEN
                ALTER TABLE exam_submissions
                ADD CONSTRAINT fk_exam_submissions_examinee_id
                FOREIGN KEY (examinee_id) REFERENCES examinees(id)
                ON DELETE SET NULL;
            END IF;
        END $$;
        """
    )

    # Keep expected index for global_table_prefs (ensure it exists)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_global_table_prefs_storage_key ON global_table_prefs (storage_key);"
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_exam_submissions_examinee_id'
            ) THEN
                ALTER TABLE exam_submissions DROP CONSTRAINT fk_exam_submissions_examinee_id;
            END IF;
        END $$;
        """
    )
    op.execute("DROP INDEX IF EXISTS idx_exam_sub_examinee;")
    op.execute("ALTER TABLE exam_submissions DROP COLUMN IF EXISTS examinee_id;")

    # Best-effort revert: make student_id NOT NULL again.
    # This may fail if NULLs exist; in that case manual cleanup is required.
    op.execute("ALTER TABLE exam_submissions ALTER COLUMN student_id SET NOT NULL;")

    op.execute("DROP INDEX IF EXISTS idx_phone_verify_expires;")
    op.execute("DROP INDEX IF EXISTS idx_phone_verify_phone;")
    op.execute("DROP TABLE IF EXISTS phone_verification_challenges;")

    op.execute("DROP INDEX IF EXISTS idx_examinees_student;")
    op.execute("DROP INDEX IF EXISTS idx_examinees_phone;")
    op.execute("DROP TABLE IF EXISTS examinees;")
