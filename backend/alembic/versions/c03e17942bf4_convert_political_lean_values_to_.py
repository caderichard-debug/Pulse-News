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
    # This migration converts uppercase political_lean enum values to lowercase.
    #
    # Challenge: ALTER TYPE ADD VALUE cannot run inside a transaction,
    # but Alembic runs migrations in transactions by default.
    #
    # Solution: Get the raw connection, check what enum values exist,
    # and add lowercase values if needed using connection.execute with autocommit

    connection = op.get_bind()

    # Step 1: Check what enum values currently exist
    result = connection.execute(text("""
        SELECT e.enumlabel
        FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'politicallean'
    """))
    existing_values = {row[0] for row in result}

    # Step 2: If we need to add lowercase values, do so outside transaction
    values_to_add = []
    if 'left' not in existing_values:
        values_to_add.append('left')
    if 'center' not in existing_values:
        values_to_add.append('center')
    if 'right' not in existing_values:
        values_to_add.append('right')

    if values_to_add:
        # We need to add enum values outside of a transaction
        # Get the raw DBAPI connection and set autocommit
        raw_connection = connection.connection
        old_isolation = raw_connection.isolation_level

        try:
            # Set autocommit mode (isolation_level = 0)
            raw_connection.set_isolation_level(0)

            cursor = raw_connection.cursor()
            for value in values_to_add:
                cursor.execute(f"ALTER TYPE politicallean ADD VALUE '{value}'")
            cursor.close()

        finally:
            # Restore original isolation level
            raw_connection.set_isolation_level(old_isolation)

    # Step 3: Convert existing data from uppercase to lowercase
    op.execute("""
        UPDATE article_analysis
        SET political_lean = 'left'::politicallean
        WHERE political_lean::text = 'LEFT'
    """)

    op.execute("""
        UPDATE article_analysis
        SET political_lean = 'center'::politicallean
        WHERE political_lean::text = 'CENTER'
    """)

    op.execute("""
        UPDATE article_analysis
        SET political_lean = 'right'::politicallean
        WHERE political_lean::text = 'RIGHT'
    """)


def downgrade() -> None:
    # Convert back to uppercase if needed (though we shouldn't need to)
    op.execute("""
        UPDATE article_analysis
        SET political_lean = 'LEFT'::politicallean
        WHERE political_lean::text = 'left'
    """)

    op.execute("""
        UPDATE article_analysis
        SET political_lean = 'CENTER'::politicallean
        WHERE political_lean::text = 'center'
    """)

    op.execute("""
        UPDATE article_analysis
        SET political_lean = 'RIGHT'::politicallean
        WHERE political_lean::text = 'right'
    """)
