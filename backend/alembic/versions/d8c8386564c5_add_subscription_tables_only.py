"""add subscription tables only

Revision ID: d8c8386564c5
Revises: f6ea9f284303
Create Date: 2025-10-26 07:49:12.739908

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8c8386564c5'
down_revision: Union[str, None] = 'f6ea9f284303'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
