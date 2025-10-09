"""Initial database schema

Revision ID: 20251009_000001
Revises:
Create Date: 2025-10-09 00:00:01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251009_000001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    processing_status = postgresql.ENUM('pending', 'processing', 'completed', 'failed', name='processingstatus', create_type=False)
    processing_status.create(op.get_bind(), checkfirst=True)

    political_lean = postgresql.ENUM('left', 'center', 'right', name='politicallean', create_type=False)
    political_lean.create(op.get_bind(), checkfirst=True)

    subscription_tier = postgresql.ENUM('free', 'premium', name='subscriptiontier', create_type=False)
    subscription_tier.create(op.get_bind(), checkfirst=True)

    verification_status = postgresql.ENUM('verified', 'unverified', 'disputed', 'false', name='verificationstatus', create_type=False)
    verification_status.create(op.get_bind(), checkfirst=True)

    verification_method = postgresql.ENUM('cross_reference', 'api_check', 'manual', 'ai_analysis', name='verificationmethod', create_type=False)
    verification_method.create(op.get_bind(), checkfirst=True)

    # Create topics table
    op.create_table('topics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_active_default', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_topics_id'), 'topics', ['id'], unique=False)
    op.create_index(op.f('ix_topics_name'), 'topics', ['name'], unique=True)

    # Create sources table
    op.create_table('sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('rss_feed_url', sa.String(length=500), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('trust_score', sa.Float(), nullable=False, server_default='0.8'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sources_id'), 'sources', ['id'], unique=False)
    op.create_index(op.f('ix_sources_name'), 'sources', ['name'], unique=False)
    op.create_index(op.f('ix_sources_rss_feed_url'), 'sources', ['rss_feed_url'], unique=True)

    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=True),
        sa.Column('subscription_tier', postgresql.ENUM('free', 'premium', name='subscriptiontier', create_type=False), nullable=False, server_default='free'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('source_discovery_mode', sa.String(length=20), nullable=False, server_default='some'),
        sa.Column('article_order_preference', sa.String(length=20), nullable=False, server_default='mixed'),
        sa.Column('articles_per_topic_default', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create frameworks table
    op.create_table('frameworks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=False),
        sa.Column('axis_description', sa.String(length=200), nullable=False),
        sa.Column('left_position', sa.String(length=200), nullable=False),
        sa.Column('right_position', sa.String(length=200), nullable=False),
        sa.Column('article_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_active', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('is_seed', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_frameworks_id'), 'frameworks', ['id'], unique=False)
    op.create_index(op.f('ix_frameworks_name'), 'frameworks', ['name'], unique=True)
    op.create_index(op.f('ix_frameworks_last_active'), 'frameworks', ['last_active'], unique=False)

    # Create articles table
    op.create_table('articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('url', sa.String(length=1000), nullable=False),
        sa.Column('author', sa.String(length=200), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=False),
        sa.Column('scraped_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('content_text', sa.String(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('extraction_method', sa.String(length=50), nullable=True),
        sa.Column('topic_category', sa.String(length=100), nullable=True),
        sa.Column('processing_status', postgresql.ENUM('pending', 'processing', 'completed', 'failed', name='processingstatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_articles_id'), 'articles', ['id'], unique=False)
    op.create_index(op.f('ix_articles_published_at'), 'articles', ['published_at'], unique=False)
    op.create_index(op.f('ix_articles_source_id'), 'articles', ['source_id'], unique=False)
    op.create_index(op.f('ix_articles_title'), 'articles', ['title'], unique=False)
    op.create_index(op.f('ix_articles_topic_category'), 'articles', ['topic_category'], unique=False)
    op.create_index(op.f('ix_articles_processing_status'), 'articles', ['processing_status'], unique=False)
    op.create_index(op.f('ix_articles_url'), 'articles', ['url'], unique=True)

    # Create newsletters table
    op.create_table('newsletters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(length=200), nullable=False),
        sa.Column('html_content', sa.String(), nullable=False, server_default=''),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('article_ids', sa.String(length=500), nullable=False, server_default='[]'),
        sa.Column('framework_ids', sa.String(length=500), nullable=False, server_default='[]'),
        sa.Column('email_opened', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('links_clicked', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_newsletters_id'), 'newsletters', ['id'], unique=False)
    op.create_index(op.f('ix_newsletters_user_id'), 'newsletters', ['user_id'], unique=False)
    op.create_index(op.f('ix_newsletters_sent_at'), 'newsletters', ['sent_at'], unique=False)

    # Create article_analysis table
    op.create_table('article_analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('summary', sa.String(length=1000), nullable=False),
        sa.Column('sentiment_score', sa.Integer(), nullable=False),
        sa.Column('political_lean', postgresql.ENUM('left', 'center', 'right', name='politicallean', create_type=False), nullable=False),
        sa.Column('bias_indicators', sa.String(length=500), nullable=True),
        sa.Column('key_stats', sa.String(), nullable=True),
        sa.Column('stats_verified', sa.Boolean(), nullable=True),
        sa.Column('stats_verification_status', postgresql.ENUM('verified', 'unverified', 'disputed', 'false', name='verificationstatus', create_type=False), nullable=False, server_default='unverified'),
        sa.Column('stats_verification_date', sa.DateTime(), nullable=True),
        sa.Column('has_context', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('processing_cost', sa.Float(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_article_analysis_id'), 'article_analysis', ['id'], unique=False)
    op.create_index(op.f('ix_article_analysis_article_id'), 'article_analysis', ['article_id'], unique=True)

    # Create statistic_verifications table
    op.create_table('statistic_verifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('statistic_text', sa.String(length=500), nullable=False),
        sa.Column('context', sa.String(length=1000), nullable=True),
        sa.Column('verification_status', postgresql.ENUM('verified', 'unverified', 'disputed', 'false', name='verificationstatus', create_type=False), nullable=False, server_default='unverified'),
        sa.Column('verification_method', postgresql.ENUM('cross_reference', 'api_check', 'manual', 'ai_analysis', name='verificationmethod', create_type=False), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('source_name', sa.String(length=200), nullable=True),
        sa.Column('source_excerpt', sa.String(length=1000), nullable=True),
        sa.Column('source_credibility_score', sa.Float(), nullable=True),
        sa.Column('fact_check_status', sa.String(length=50), nullable=True),
        sa.Column('fact_check_source', sa.String(length=100), nullable=True),
        sa.Column('fact_check_url', sa.String(length=500), nullable=True),
        sa.Column('fact_check_details', sa.String(length=2000), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('last_checked', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_statistic_verifications_article_id'), 'statistic_verifications', ['article_id'], unique=False)

    # Create article_clusters table
    op.create_table('article_clusters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cluster_hash', sa.String(length=64), nullable=False),
        sa.Column('primary_topic', sa.String(length=200), nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_article_clusters_cluster_hash'), 'article_clusters', ['cluster_hash'], unique=True)
    op.create_index(op.f('ix_article_clusters_primary_topic'), 'article_clusters', ['primary_topic'], unique=False)

    # Create article_context table
    op.create_table('article_context',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('background', sa.String(length=2000), nullable=True),
        sa.Column('key_players', sa.String(), nullable=True),
        sa.Column('timeline', sa.String(), nullable=True),
        sa.Column('significance', sa.String(length=1000), nullable=True),
        sa.Column('next_developments', sa.String(length=1000), nullable=True),
        sa.Column('sources_consulted', sa.String(), nullable=True),
        sa.Column('context_quality_score', sa.Float(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_article_context_article_id'), 'article_context', ['article_id'], unique=True)

    # Create source_credibility_ratings table
    op.create_table('source_credibility_ratings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('domain', sa.String(length=200), nullable=False),
        sa.Column('credibility_score', sa.Float(), nullable=False),
        sa.Column('is_academic', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_government', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_news_organization', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_think_tank', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('rating_method', sa.String(length=100), nullable=False),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_source_credibility_ratings_domain'), 'source_credibility_ratings', ['domain'], unique=True)

    # Create link tables
    op.create_table('source_topics',
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ),
        sa.PrimaryKeyConstraint('source_id', 'topic_id')
    )

    op.create_table('article_topics',
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ),
        sa.PrimaryKeyConstraint('article_id', 'topic_id')
    )

    op.create_table('newsletter_articles',
        sa.Column('newsletter_id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.ForeignKeyConstraint(['newsletter_id'], ['newsletters.id'], ),
        sa.PrimaryKeyConstraint('newsletter_id', 'article_id')
    )

    op.create_table('article_frameworks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('framework_id', sa.Integer(), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=False),
        sa.Column('position_on_axis', sa.Integer(), nullable=False),
        sa.Column('ai_explanation', sa.String(length=500), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.ForeignKeyConstraint(['framework_id'], ['frameworks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_article_frameworks_article_id'), 'article_frameworks', ['article_id'], unique=False)
    op.create_index(op.f('ix_article_frameworks_framework_id'), 'article_frameworks', ['framework_id'], unique=False)

    op.create_table('user_topic_preferences',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('priority_level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('include_in_newsletter', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('articles_per_topic', sa.Integer(), nullable=False, server_default='5'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'topic_id')
    )

    op.create_table('user_source_subscriptions',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('subscribed', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'source_id')
    )

    op.create_table('article_cluster_members',
        sa.Column('cluster_id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.ForeignKeyConstraint(['cluster_id'], ['article_clusters.id'], ),
        sa.PrimaryKeyConstraint('cluster_id', 'article_id')
    )


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table('article_cluster_members')
    op.drop_table('user_source_subscriptions')
    op.drop_table('user_topic_preferences')
    op.drop_index(op.f('ix_article_frameworks_framework_id'), table_name='article_frameworks')
    op.drop_index(op.f('ix_article_frameworks_article_id'), table_name='article_frameworks')
    op.drop_table('article_frameworks')
    op.drop_table('newsletter_articles')
    op.drop_table('article_topics')
    op.drop_table('source_topics')
    op.drop_index(op.f('ix_source_credibility_ratings_domain'), table_name='source_credibility_ratings')
    op.drop_table('source_credibility_ratings')
    op.drop_index(op.f('ix_article_context_article_id'), table_name='article_context')
    op.drop_table('article_context')
    op.drop_index(op.f('ix_article_clusters_primary_topic'), table_name='article_clusters')
    op.drop_index(op.f('ix_article_clusters_cluster_hash'), table_name='article_clusters')
    op.drop_table('article_clusters')
    op.drop_index(op.f('ix_statistic_verifications_article_id'), table_name='statistic_verifications')
    op.drop_table('statistic_verifications')
    op.drop_index(op.f('ix_article_analysis_article_id'), table_name='article_analysis')
    op.drop_index(op.f('ix_article_analysis_id'), table_name='article_analysis')
    op.drop_table('article_analysis')
    op.drop_index(op.f('ix_newsletters_sent_at'), table_name='newsletters')
    op.drop_index(op.f('ix_newsletters_user_id'), table_name='newsletters')
    op.drop_index(op.f('ix_newsletters_id'), table_name='newsletters')
    op.drop_table('newsletters')
    op.drop_index(op.f('ix_articles_url'), table_name='articles')
    op.drop_index(op.f('ix_articles_processing_status'), table_name='articles')
    op.drop_index(op.f('ix_articles_topic_category'), table_name='articles')
    op.drop_index(op.f('ix_articles_title'), table_name='articles')
    op.drop_index(op.f('ix_articles_source_id'), table_name='articles')
    op.drop_index(op.f('ix_articles_published_at'), table_name='articles')
    op.drop_index(op.f('ix_articles_id'), table_name='articles')
    op.drop_table('articles')
    op.drop_index(op.f('ix_frameworks_last_active'), table_name='frameworks')
    op.drop_index(op.f('ix_frameworks_name'), table_name='frameworks')
    op.drop_index(op.f('ix_frameworks_id'), table_name='frameworks')
    op.drop_table('frameworks')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_sources_rss_feed_url'), table_name='sources')
    op.drop_index(op.f('ix_sources_name'), table_name='sources')
    op.drop_index(op.f('ix_sources_id'), table_name='sources')
    op.drop_table('sources')
    op.drop_index(op.f('ix_topics_name'), table_name='topics')
    op.drop_index(op.f('ix_topics_id'), table_name='topics')
    op.drop_table('topics')

    # Drop enum types
    postgresql.ENUM(name='verificationmethod').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='verificationstatus').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='subscriptiontier').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='politicallean').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='processingstatus').drop(op.get_bind(), checkfirst=True)
