"""add_newsletter_challenge_system

Revision ID: 3a2b4c5d6e7f
Revises: e7b694a129c8
Create Date: 2025-10-23 03:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3a2b4c5d6e7f'
down_revision: Union[str, None] = '3fff820c56d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add challenge_participation_enabled to users table
    op.add_column('users', sa.Column('challenge_participation_enabled', sa.Boolean(), nullable=False, server_default='true'))

    # Create weekly_challenges table
    op.create_table('weekly_challenges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('week_start_date', sa.DateTime(), nullable=False),
        sa.Column('week_end_date', sa.DateTime(), nullable=False),
        sa.Column('challenge_date', sa.DateTime(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('total_participants', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('generation_method', sa.String(length=50), nullable=False, server_default='automatic'),
        sa.Column('ai_model_version', sa.String(length=50), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('admin_notes', sa.String(length=1000), nullable=True),
        sa.Column('last_reviewed_by', sa.Integer(), nullable=True),
        sa.Column('last_reviewed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['last_reviewed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_challenge_week', 'weekly_challenges', ['week_start_date', 'week_end_date'], unique=False)
    op.create_index('idx_challenge_date', 'weekly_challenges', ['challenge_date'], unique=False)
    op.create_index('idx_active_challenges', 'weekly_challenges', ['is_active', 'is_published'], unique=False)

    # Create challenge_claims table
    op.create_table('challenge_claims',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('weekly_challenge_id', sa.Integer(), nullable=False),
        sa.Column('claim_text', sa.String(length=300), nullable=False),
        sa.Column('claim_type', sa.Enum('POLICY', 'SOCIAL_ISSUE', 'ECONOMIC', 'TECHNOLOGY', 'ENVIRONMENT', 'FOREIGN_POLICY', 'HEALTHCARE', 'EDUCATION', name='challengeclaimtype'), nullable=False),
        sa.Column('background_context', sa.String(length=1000), nullable=True),
        sa.Column('key_statistics', sa.String(length=1000), nullable=True),
        sa.Column('political_lean_distribution', sa.String(length=200), nullable=True),
        sa.Column('controversy_score', sa.Float(), nullable=True),
        sa.Column('reasonableness_score', sa.Float(), nullable=True),
        sa.Column('source_article_id', sa.Integer(), nullable=True),
        sa.Column('source_topic_ids', sa.String(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('generation_method', sa.String(length=50), nullable=False, server_default='automatic'),
        sa.Column('ai_prompt_used', sa.String(length=2000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['source_article_id'], ['articles.id'], ),
        sa.ForeignKeyConstraint(['weekly_challenge_id'], ['weekly_challenges.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_weekly_challenge_claims', 'challenge_claims', ['weekly_challenge_id', 'display_order'], unique=False)
    op.create_index('idx_claim_type', 'challenge_claims', ['claim_type'], unique=False)
    op.create_index('idx_claim_controversy', 'challenge_claims', ['controversy_score', 'is_active'], unique=False)

    # Create user_challenge_responses table
    op.create_table('user_challenge_responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('weekly_challenge_id', sa.Integer(), nullable=False),
        sa.Column('selected_claim_id', sa.Integer(), nullable=False),
        sa.Column('agreement_level', sa.Enum('STRONGLY_DISAGREE', 'DISAGREE', 'NEUTRAL', 'AGREE', 'STRONGLY_AGREE', name='agreementlevel'), nullable=False),
        sa.Column('response_time_seconds', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'RESPONDED', 'COMPLETED', 'SKIPPED', name='challengeresponsestatus'), nullable=False, server_default='pending'),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.Column('response_source', sa.String(length=50), nullable=False, server_default='newsletter'),
        sa.Column('challenge_started_at', sa.DateTime(), nullable=True),
        sa.Column('challenge_completed_at', sa.DateTime(), nullable=True),
        sa.Column('articles_sent_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('articles_engaged_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('found_valuable', sa.Boolean(), nullable=True),
        sa.Column('feedback_text', sa.String(length=1000), nullable=True),
        sa.Column('opted_out_future', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['selected_claim_id'], ['challenge_claims.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['weekly_challenge_id'], ['weekly_challenges.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'weekly_challenge_id', name='uq_user_weekly_challenge')
    )
    op.create_index('idx_user_weekly_response', 'user_challenge_responses', ['user_id', 'weekly_challenge_id'], unique=False)
    op.create_index('idx_user_selected_claim', 'user_challenge_responses', ['user_id', 'selected_claim_id'], unique=False)
    op.create_index('idx_response_status', 'user_challenge_responses', ['status', 'responded_at'], unique=False)
    op.create_index('idx_challenge_tracking', 'user_challenge_responses', ['challenge_started_at', 'challenge_completed_at'], unique=False)

    # Create challenge_article_assignments table
    op.create_table('challenge_article_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_challenge_response_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('assignment_date', sa.DateTime(), nullable=False),
        sa.Column('opposition_strength', sa.Float(), nullable=False),
        sa.Column('match_algorithm', sa.String(length=50), nullable=False),
        sa.Column('match_reasoning', sa.String(length=1000), nullable=True),
        sa.Column('is_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivery_method', sa.String(length=50), nullable=False, server_default='newsletter'),
        sa.Column('is_opened', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('is_clicked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('clicked_at', sa.DateTime(), nullable=True),
        sa.Column('time_to_click_seconds', sa.Integer(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('user_feedback_helpful', sa.Boolean(), nullable=True),
        sa.Column('user_reported_inappropriate', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.ForeignKeyConstraint(['user_challenge_response_id'], ['user_challenge_responses.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_challenge_response_id', 'day_number', name='uq_user_challenge_day'),
        sa.CheckConstraint('day_number >= 1 AND day_number <= 7', name='check_day_number_range')
    )
    op.create_index('idx_user_challenge_assignments', 'challenge_article_assignments', ['user_challenge_response_id', 'day_number'], unique=False)
    op.create_index('idx_user_daily_assignment', 'challenge_article_assignments', ['user_id', 'assignment_date'], unique=False)
    op.create_index('idx_assignment_status', 'challenge_article_assignments', ['is_sent', 'is_opened', 'is_clicked'], unique=False)
    op.create_index('idx_article_assignments', 'challenge_article_assignments', ['article_id', 'assignment_date'], unique=False)

    # Create challenge_engagements table
    op.create_table('challenge_engagements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('challenge_assignment_id', sa.Integer(), nullable=False),
        sa.Column('engagement_type', sa.String(length=50), nullable=False),
        sa.Column('engagement_value', sa.String(length=1000), nullable=True),
        sa.Column('engagement_time_seconds', sa.Integer(), nullable=True),
        sa.Column('device_type', sa.String(length=50), nullable=True),
        sa.Column('referrer', sa.String(length=200), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('ip_address_hash', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['challenge_assignment_id'], ['challenge_article_assignments.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_challenge_engagement', 'challenge_engagements', ['user_id', 'challenge_assignment_id'], unique=False)
    op.create_index('idx_engagement_type', 'challenge_engagements', ['engagement_type', 'created_at'], unique=False)
    op.create_index('idx_engagement_timing', 'challenge_engagements', ['created_at', 'engagement_time_seconds'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_index('idx_engagement_timing', table_name='challenge_engagements')
    op.drop_index('idx_engagement_type', table_name='challenge_engagements')
    op.drop_index('idx_user_challenge_engagement', table_name='challenge_engagements')
    op.drop_table('challenge_engagements')

    op.drop_index('idx_article_assignments', table_name='challenge_article_assignments')
    op.drop_index('idx_assignment_status', table_name='challenge_article_assignments')
    op.drop_index('idx_user_daily_assignment', table_name='challenge_article_assignments')
    op.drop_index('idx_user_challenge_assignments', table_name='challenge_article_assignments')
    op.drop_table('challenge_article_assignments')

    op.drop_index('idx_challenge_tracking', table_name='user_challenge_responses')
    op.drop_index('idx_response_status', table_name='user_challenge_responses')
    op.drop_index('idx_user_selected_claim', table_name='user_challenge_responses')
    op.drop_index('idx_user_weekly_response', table_name='user_challenge_responses')
    op.drop_table('user_challenge_responses')

    op.drop_index('idx_claim_controversy', table_name='challenge_claims')
    op.drop_index('idx_claim_type', table_name='challenge_claims')
    op.drop_index('idx_weekly_challenge_claims', table_name='challenge_claims')
    op.drop_table('challenge_claims')

    op.drop_index('idx_active_challenges', table_name='weekly_challenges')
    op.drop_index('idx_challenge_date', table_name='weekly_challenges')
    op.drop_index('idx_challenge_week', table_name='weekly_challenges')
    op.drop_table('weekly_challenges')

    # Remove challenge_participation_enabled from users table
    op.drop_column('users', 'challenge_participation_enabled')