"""Add newsletter enhancement tables and fields

Revision ID: de529afde6ed
Revises: 3b13d7392dd2
Create Date: 2025-10-02 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'de529afde6ed'
down_revision: Union[str, None] = '3b13d7392dd2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    verification_status_enum = postgresql.ENUM('VERIFIED', 'UNVERIFIED', 'DISPUTED', 'FALSE', name='verificationstatus')
    verification_status_enum.create(op.get_bind(), checkfirst=True)

    verification_method_enum = postgresql.ENUM('CROSS_REFERENCE', 'API_CHECK', 'MANUAL', 'AI_ANALYSIS', name='verificationmethod')
    verification_method_enum.create(op.get_bind(), checkfirst=True)

    # Create new tables
    op.create_table(
        'statistic_verifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('statistic_text', sa.String(length=500), nullable=False),
        sa.Column('verification_status', verification_status_enum, nullable=False, server_default='UNVERIFIED'),
        sa.Column('verification_method', verification_method_enum, nullable=True),
        sa.Column('verified_sources', sa.String(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('verified_by', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_statistic_verifications_article_id'), 'statistic_verifications', ['article_id'], unique=False)

    op.create_table(
        'article_clusters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cluster_hash', sa.String(length=64), nullable=False),
        sa.Column('primary_topic', sa.String(length=200), nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cluster_hash')
    )
    op.create_index(op.f('ix_article_clusters_cluster_hash'), 'article_clusters', ['cluster_hash'], unique=True)
    op.create_index(op.f('ix_article_clusters_primary_topic'), 'article_clusters', ['primary_topic'], unique=False)

    op.create_table(
        'article_context',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('background', sa.String(length=2000), nullable=True),
        sa.Column('key_players', sa.String(), nullable=True),
        sa.Column('timeline', sa.String(), nullable=True),
        sa.Column('significance', sa.String(length=1000), nullable=True),
        sa.Column('next_developments', sa.String(length=1000), nullable=True),
        sa.Column('sources_consulted', sa.String(), nullable=True),
        sa.Column('context_quality_score', sa.Float(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('article_id')
    )
    op.create_index(op.f('ix_article_context_article_id'), 'article_context', ['article_id'], unique=True)

    op.create_table(
        'article_cluster_members',
        sa.Column('cluster_id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.ForeignKeyConstraint(['cluster_id'], ['article_clusters.id'], ),
        sa.PrimaryKeyConstraint('cluster_id', 'article_id')
    )

    # Add new columns to article_analysis (with server defaults for existing rows)
    with op.batch_alter_table('article_analysis', schema=None) as batch_op:
        batch_op.add_column(sa.Column('stats_verification_status', verification_status_enum, nullable=False, server_default='UNVERIFIED'))
        batch_op.add_column(sa.Column('stats_verification_date', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('has_context', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Drop new columns from article_analysis
    with op.batch_alter_table('article_analysis', schema=None) as batch_op:
        batch_op.drop_column('has_context')
        batch_op.drop_column('stats_verification_date')
        batch_op.drop_column('stats_verification_status')

    # Drop new tables
    op.drop_table('article_cluster_members')
    op.drop_index(op.f('ix_article_context_article_id'), table_name='article_context')
    op.drop_table('article_context')
    op.drop_index(op.f('ix_article_clusters_primary_topic'), table_name='article_clusters')
    op.drop_index(op.f('ix_article_clusters_cluster_hash'), table_name='article_clusters')
    op.drop_table('article_clusters')
    op.drop_index(op.f('ix_statistic_verifications_article_id'), table_name='statistic_verifications')
    op.drop_table('statistic_verifications')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS verificationmethod')
    op.execute('DROP TYPE IF EXISTS verificationstatus')
