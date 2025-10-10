"""update_processing_status_enum_to_uppercase

Revision ID: ae55c7bb7c8f
Revises: 20251009_000001
Create Date: 2025-10-10 16:00:22.622451

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae55c7bb7c8f'
down_revision: Union[str, None] = '20251009_000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the default value first (it references the old enum type)
    op.execute("ALTER TABLE articles ALTER COLUMN processing_status DROP DEFAULT")

    # Rename old enum type
    op.execute("ALTER TYPE processingstatus RENAME TO processingstatus_old")

    # Create new enum type with uppercase values
    op.execute("CREATE TYPE processingstatus AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')")

    # Update column to use new enum type with uppercase conversion
    op.execute("""
        ALTER TABLE articles
        ALTER COLUMN processing_status TYPE processingstatus
        USING UPPER(processing_status::text)::processingstatus
    """)

    # Drop old enum type
    op.execute("DROP TYPE processingstatus_old")

    # Re-add the default value with uppercase
    op.execute("ALTER TABLE articles ALTER COLUMN processing_status SET DEFAULT 'PENDING'::processingstatus")


def downgrade() -> None:
    # Drop the default value first
    op.execute("ALTER TABLE articles ALTER COLUMN processing_status DROP DEFAULT")

    # Rename current enum type
    op.execute("ALTER TYPE processingstatus RENAME TO processingstatus_new")

    # Recreate old enum type with lowercase values
    op.execute("CREATE TYPE processingstatus AS ENUM ('pending', 'processing', 'completed', 'failed')")

    # Update column to use old enum type and convert to lowercase
    op.execute("""
        ALTER TABLE articles
        ALTER COLUMN processing_status TYPE processingstatus
        USING LOWER(processing_status::text)::processingstatus
    """)

    # Drop new enum type
    op.execute("DROP TYPE processingstatus_new")

    # Re-add the default value with lowercase
    op.execute("ALTER TABLE articles ALTER COLUMN processing_status SET DEFAULT 'pending'::processingstatus")
