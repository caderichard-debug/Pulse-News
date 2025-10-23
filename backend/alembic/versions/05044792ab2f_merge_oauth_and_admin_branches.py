"""merge_oauth_and_admin_branches

Revision ID: 05044792ab2f
Revises: 3fff820c56d0, bb65738374e1
Create Date: 2025-10-22 19:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05044792ab2f'
down_revision: Union[str, None] = ('3fff820c56d0', 'bb65738374e1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass