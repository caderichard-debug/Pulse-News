"""add_unique_constraint_article_framework_clean

Revision ID: 7f71518740d3
Revises: c03e17942bf4
Create Date: 2025-10-12 16:08:57.933328

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f71518740d3'
down_revision: Union[str, None] = 'c03e17942bf4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add unique constraint to prevent duplicate article-framework links
    # First, remove any existing duplicates (keep the one with lowest id)
    op.execute("""
        DELETE FROM article_frameworks
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM article_frameworks
            GROUP BY article_id, framework_id
        )
    """)

    # Then add the unique constraint
    op.create_unique_constraint(
        'uq_article_framework',
        'article_frameworks',
        ['article_id', 'framework_id']
    )


def downgrade() -> None:
    op.drop_constraint('uq_article_framework', 'article_frameworks', type_='unique')
