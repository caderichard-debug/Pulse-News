"""add_source_bias_fields

Revision ID: e29da670f9de
Revises: 052b74d0175f
Create Date: 2025-10-13 05:06:44.272003

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e29da670f9de'
down_revision: Union[str, None] = '052b74d0175f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the enum type first
    organizationalbias_enum = sa.Enum('left', 'center-left', 'center', 'center-right', 'right', name='organizationalbias')
    organizationalbias_enum.create(op.get_bind(), checkfirst=True)
    
    # Add columns
    with op.batch_alter_table('sources', schema=None) as batch_op:
        batch_op.add_column(sa.Column('organizational_bias', organizationalbias_enum, nullable=True))
        batch_op.add_column(sa.Column('bias_description', sa.String(length=500), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('sources', schema=None) as batch_op:
        batch_op.drop_column('bias_description')
        batch_op.drop_column('organizational_bias')
    
    # Drop the enum type
    sa.Enum(name='organizationalbias').drop(op.get_bind(), checkfirst=True)
