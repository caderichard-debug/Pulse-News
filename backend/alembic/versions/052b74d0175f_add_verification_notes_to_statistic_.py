"""add_verification_notes_to_statistic_verifications

Revision ID: 052b74d0175f
Revises: 7f71518740d3
Create Date: 2025-10-12 16:39:24.738233

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '052b74d0175f'
down_revision: Union[str, None] = '7f71518740d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add verification_notes column
    op.add_column('statistic_verifications',
        sa.Column('verification_notes', sa.String(length=500), nullable=True)
    )


def downgrade() -> None:
    # Remove verification_notes column
    op.drop_column('statistic_verifications', 'verification_notes')
