"""merge challenge system updates

Revision ID: 31f70ab13ba5
Revises: 05044792ab2f, 3a2b4c5d6e7f
Create Date: 2025-10-23 04:18:56.656032

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '31f70ab13ba5'
down_revision: Union[str, None] = ('05044792ab2f', '3a2b4c5d6e7f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
