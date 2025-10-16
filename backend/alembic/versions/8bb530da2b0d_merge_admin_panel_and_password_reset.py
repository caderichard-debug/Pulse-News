"""merge_admin_panel_and_password_reset

Revision ID: 8bb530da2b0d
Revises: bb65738374e1, d765e2a06a7d
Create Date: 2025-10-16 01:11:02.282176

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8bb530da2b0d'
down_revision: Union[str, None] = ('bb65738374e1', 'd765e2a06a7d')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
