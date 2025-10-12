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

    # Update article_analysis table
    # Note: We need to cast the enum to text before using LOWER()
    op.execute("""
        UPDATE article_analysis
        SET political_lean = LOWER(political_lean::text)::politicallean
        WHERE political_lean::text IN ('LEFT', 'CENTER', 'RIGHT')
    """)


def downgrade() -> None:
    # Convert back to uppercase if needed (though we shouldn't need to)
    op.execute("""
        UPDATE article_analysis
        SET political_lean = UPPER(political_lean::text)::politicallean
        WHERE political_lean::text IN ('left', 'center', 'right')
    """)
