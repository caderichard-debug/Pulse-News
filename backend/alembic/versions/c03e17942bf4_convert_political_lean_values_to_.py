"""convert_political_lean_values_to_lowercase

Revision ID: c03e17942bf4
Revises: ae55c7bb7c8f
Create Date: 2025-10-11 21:23:25.794620

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'c03e17942bf4'
down_revision: Union[str, None] = 'ae55c7bb7c8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This migration handles production databases that may have uppercase enum values.
    # The initial schema migration creates lowercase values, but production was created
    # with uppercase values before migrations were added.

    connection = op.get_bind()

    # Check if we need to add lowercase enum values
    result = connection.execute(text("""
        SELECT e.enumlabel
        FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'politicallean'
    """))
    existing_values = {row[0] for row in result}

    # Add missing lowercase values using autocommit (required for ALTER TYPE ADD VALUE)
    values_needed = {'left', 'center', 'right'} - existing_values

    if values_needed:
        raw_connection = connection.connection
        old_isolation = raw_connection.isolation_level

        try:
            raw_connection.set_isolation_level(0)  # autocommit mode
            cursor = raw_connection.cursor()
            for value in sorted(values_needed):  # sorted for consistency
                cursor.execute(f"ALTER TYPE politicallean ADD VALUE '{value}'")
            cursor.close()
        finally:
            raw_connection.set_isolation_level(old_isolation)

    # Convert any uppercase data to lowercase
    op.execute("""
        UPDATE article_analysis
        SET political_lean = LOWER(political_lean::text)::politicallean
        WHERE political_lean::text IN ('LEFT', 'CENTER', 'RIGHT')
    """)


def downgrade() -> None:
    # Convert back to uppercase (though this should rarely be needed)
    op.execute("""
        UPDATE article_analysis
        SET political_lean = UPPER(political_lean::text)::politicallean
        WHERE political_lean::text IN ('left', 'center', 'right')
    """)
