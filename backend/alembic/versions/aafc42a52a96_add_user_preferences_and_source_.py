"""add_user_preferences_and_source_subscriptions

Revision ID: aafc42a52a96
Revises: 3b13d7392dd2
Create Date: 2025-10-04 01:33:29.289736

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aafc42a52a96'
down_revision: Union[str, None] = 'd819e76d0940'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add preference columns to users table
    op.add_column('users', sa.Column('source_discovery_mode', sa.String(length=20), nullable=True, server_default='some'))
    op.add_column('users', sa.Column('article_order_preference', sa.String(length=20), nullable=True, server_default='mixed'))
    op.add_column('users', sa.Column('articles_per_topic_default', sa.Integer(), nullable=True, server_default='5'))

    # Create user_source_subscriptions table
    op.create_table(
        'user_source_subscriptions',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('subscribed', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'source_id')
    )

    # Add articles_per_topic column to user_topic_preferences
    op.add_column('user_topic_preferences', sa.Column('articles_per_topic', sa.Integer(), nullable=True, server_default='5'))


def downgrade() -> None:
    # Remove articles_per_topic from user_topic_preferences
    op.drop_column('user_topic_preferences', 'articles_per_topic')

    # Drop user_source_subscriptions table
    op.drop_table('user_source_subscriptions')

    # Remove preference columns from users table
    op.drop_column('users', 'articles_per_topic_default')
    op.drop_column('users', 'article_order_preference')
    op.drop_column('users', 'source_discovery_mode')
