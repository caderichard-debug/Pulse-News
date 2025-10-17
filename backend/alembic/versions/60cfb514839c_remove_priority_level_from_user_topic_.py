"""remove_priority_level_from_user_topic_preferences

Revision ID: 60cfb514839c
Revises: 8bb530da2b0d
Create Date: 2025-10-17 04:05:50.886574

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60cfb514839c'
down_revision: Union[str, None] = '8bb530da2b0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove priority_level column from user_topic_preferences table
    op.drop_column('user_topic_preferences', 'priority_level')


def downgrade() -> None:
    # Re-add priority_level column if we need to rollback
    op.add_column('user_topic_preferences',
        sa.Column('priority_level', sa.Integer(), nullable=False, server_default='1')
    )
