"""add_unique_constraint_article_framework_clean

Revision ID: 7f71518740d3
Revises: 7e947d383738
Create Date: 2025-10-12 16:08:57.933328

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f71518740d3'
down_revision: Union[str, None] = '7e947d383738'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This migration is a no-op because the unique constraint was already
    # added in migration 7e947d383738. This migration file is kept for
    # compatibility with the migration history but performs no operations.
    pass


def downgrade() -> None:
    # No downgrade needed since upgrade is a no-op
    pass
