"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2025-10-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    processing_status_enum = postgresql.ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='processingstatus')
    processing_status_enum.create(op.get_bind(), checkfirst=True)

    political_lean_enum = postgresql.ENUM('FAR_LEFT', 'LEFT', 'CENTER_LEFT', 'CENTER', 'CENTER_RIGHT', 'RIGHT', 'FAR_RIGHT', name='politicallean')
    political_lean_enum.create(op.get_bind(), checkfirst=True)

    subscription_tier_enum = postgresql.ENUM('FREE', 'BASIC', 'PREMIUM', name='subscriptiontier')
    subscription_tier_enum.create(op.get_bind(), checkfirst=True)

    # Create topics table
    op.create_table('topics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_topics_id'), 'topics', ['id'], unique=False)
    op.create_index(op.f('ix_topics_name'), 'topics', ['name'], unique=True)

    # Create sources table
    op.create_table('sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('rss_url', sa.String(), nullable=False),
        sa.Column('political_lean', postgresql.ENUM('FAR_LEFT', 'LEFT', 'CENTER_LEFT', 'CENTER', 'CENTER_RIGHT', 'RIGHT', 'FAR_RIGHT', name='politicallean'), nullable=True),
        sa.Column('credibility_score', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sources_id'), 'sources', ['id'], unique=False)
    op.create_index(op.f('ix_sources_name'), 'sources', ['name'], unique=True)

    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('subscription_tier', postgresql.ENUM('FREE', 'BASIC', 'PREMIUM', name='subscriptiontier'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('newsletter_frequency', sa.String(), nullable=True),
        sa.Column('min_credibility_threshold', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create frameworks table
    op.create_table('frameworks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_frameworks_id'), 'frameworks', ['id'], unique=False)
    op.create_index(op.f('ix_frameworks_name'), 'frameworks', ['name'], unique=True)

    # Create articles table
    op.create_table('articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=False),
        sa.Column('content', sa.String(), nullable=True),
        sa.Column('scraped_at', sa.DateTime(), nullable=True),
        sa.Column('processing_status', postgresql.ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='processingstatus'), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_articles_id'), 'articles', ['id'], unique=False)
    op.create_index(op.f('ix_articles_published_at'), 'articles', ['published_at'], unique=False)
    op.create_index(op.f('ix_articles_url'), 'articles', ['url'], unique=True)

    # Create newsletters table
    op.create_table('newsletters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_newsletters_id'), 'newsletters', ['id'], unique=False)

    # Create article_analyses table
    op.create_table('article_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('summary', sa.String(), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('bias_score', sa.Float(), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_article_analyses_id'), 'article_analyses', ['id'], unique=False)

    # Create link tables
    op.create_table('source_topic_links',
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ),
        sa.PrimaryKeyConstraint('source_id', 'topic_id')
    )

    op.create_table('article_topic_links',
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ),
        sa.PrimaryKeyConstraint('article_id', 'topic_id')
    )

    op.create_table('article_framework_links',
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('framework_id', sa.Integer(), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.ForeignKeyConstraint(['framework_id'], ['frameworks.id'], ),
        sa.PrimaryKeyConstraint('article_id', 'framework_id')
    )

    op.create_table('newsletter_articles',
        sa.Column('newsletter_id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.ForeignKeyConstraint(['newsletter_id'], ['newsletters.id'], ),
        sa.PrimaryKeyConstraint('newsletter_id', 'article_id')
    )

    op.create_table('user_topic_preferences',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'topic_id')
    )

    op.create_table('user_source_subscriptions',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('subscribed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'source_id')
    )


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table('user_source_subscriptions')
    op.drop_table('user_topic_preferences')
    op.drop_table('newsletter_articles')
    op.drop_table('article_framework_links')
    op.drop_table('article_topic_links')
    op.drop_table('source_topic_links')
    op.drop_table('article_analyses')
    op.drop_table('newsletters')
    op.drop_table('articles')
    op.drop_table('frameworks')
    op.drop_table('users')
    op.drop_table('sources')
    op.drop_table('topics')

    # Drop enum types
    postgresql.ENUM(name='subscriptiontier').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='politicallean').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='processingstatus').drop(op.get_bind(), checkfirst=True)
