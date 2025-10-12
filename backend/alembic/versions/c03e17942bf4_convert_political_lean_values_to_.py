"""convert_political_lean_values_to_lowercase

Revision ID: c03e17942bf4
Revises: ae55c7bb7c8f
Create Date: 2025-10-11 21:23:25.794620

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c03e17942bf4'
down_revision: Union[str, None] = 'ae55c7bb7c8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert all existing political_lean values from uppercase to lowercase
    # This fixes the LookupError where SQLAlchemy can't find uppercase enum values

    # Step 1: Add lowercase values to the enum type
    # PostgreSQL requires ALTER TYPE ADD VALUE for each new enum value
    op.execute("ALTER TYPE politicallean ADD VALUE IF NOT EXISTS 'left'")
    op.execute("ALTER TYPE politicallean ADD VALUE IF NOT EXISTS 'center'")
    op.execute("ALTER TYPE politicallean ADD VALUE IF NOT EXISTS 'right'")

    # Step 2: Convert existing data to lowercase
    # Map uppercase to lowercase values
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
