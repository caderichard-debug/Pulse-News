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
    # Create all enum types if they don't exist
    try:
        # Create challengeclaimtype enum (lowercase values for consistency)
        op.execute("DO $$ BEGIN\n"
                   "    CREATE TYPE challengeclaimtype AS ENUM ('policy', 'social_issue', 'economic', 'technology', 'environment', 'foreign_policy', 'healthcare', 'education');\n"
                   "EXCEPTION\n"
                   "    WHEN duplicate_object THEN null;\n"
                   "END $$;")
    except Exception:
        pass  # Enum already exists

    try:
        # Create challengeresponsestatus enum (lowercase values for consistency)
        op.execute("DO $$ BEGIN\n"
                   "    CREATE TYPE challengeresponsestatus AS ENUM ('pending', 'responded', 'completed', 'skipped');\n"
                   "EXCEPTION\n"
                   "    WHEN duplicate_object THEN null;\n"
                   "END $$;")
    except Exception:
        pass  # Enum already exists

    try:
        # Create agreementlevel enum (uppercase values as it doesn't exist yet)
        op.execute("DO $$ BEGIN\n"
                   "    CREATE TYPE agreementlevel AS ENUM ('STRONGLY_DISAGREE', 'DISAGREE', 'NEUTRAL', 'AGREE', 'STRONGLY_AGREE');\n"
                   "EXCEPTION\n"
                   "    WHEN duplicate_object THEN null;\n"
                   "END $$;")
    except Exception:
        pass  # Enum already exists

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
    op.execute("""
        CREATE TABLE IF NOT EXISTS challenge_claims (
            id SERIAL NOT NULL,
            weekly_challenge_id INTEGER NOT NULL,
            claim_text VARCHAR(300) NOT NULL,
            claim_type challengeclaimtype NOT NULL,
            background_context VARCHAR(1000),
            key_statistics VARCHAR(1000),
            political_lean_distribution VARCHAR(200),
            controversy_score FLOAT,
            reasonableness_score FLOAT,
            source_article_id INTEGER,
            source_topic_ids TEXT,
            display_order INTEGER DEFAULT '0' NOT NULL,
            is_active BOOLEAN DEFAULT 'true' NOT NULL,
            generation_method VARCHAR(50) DEFAULT 'automatic' NOT NULL,
            ai_prompt_used VARCHAR(2000),
            created_at TIMESTAMP DEFAULT now() NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(source_article_id) REFERENCES articles(id),
            FOREIGN KEY(weekly_challenge_id) REFERENCES weekly_challenges(id)
        )
    """)

    # Create indexes for challenge_claims
    op.execute("CREATE INDEX IF NOT EXISTS idx_weekly_challenge_claims ON challenge_claims (weekly_challenge_id, display_order)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_claim_type ON challenge_claims (claim_type)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_claim_controversy ON challenge_claims (controversy_score, is_active)")

    # Create user_challenge_responses table
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_challenge_responses (
            id SERIAL NOT NULL,
            user_id INTEGER NOT NULL,
            weekly_challenge_id INTEGER NOT NULL,
            selected_claim_id INTEGER NOT NULL,
            agreement_level agreementlevel NOT NULL,
            response_time_seconds INTEGER,
            status challengeresponsestatus DEFAULT 'pending' NOT NULL,
            responded_at TIMESTAMP,
            response_source VARCHAR(50) DEFAULT 'newsletter' NOT NULL,
            challenge_started_at TIMESTAMP,
            challenge_completed_at TIMESTAMP,
            articles_sent_count INTEGER DEFAULT '0' NOT NULL,
            articles_engaged_count INTEGER DEFAULT '0' NOT NULL,
            found_valuable BOOLEAN,
            feedback_text VARCHAR(1000),
            opted_out_future BOOLEAN DEFAULT 'false' NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(selected_claim_id) REFERENCES challenge_claims(id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(weekly_challenge_id) REFERENCES weekly_challenges(id),
            CONSTRAINT uq_user_weekly_challenge UNIQUE (user_id, weekly_challenge_id)
        )
    """)

    # Create indexes for user_challenge_responses
    op.execute("CREATE INDEX IF NOT EXISTS idx_user_weekly_response ON user_challenge_responses (user_id, weekly_challenge_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_user_selected_claim ON user_challenge_responses (user_id, selected_claim_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_response_status ON user_challenge_responses (status, responded_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_challenge_tracking ON user_challenge_responses (challenge_started_at, challenge_completed_at)")

    # Create challenge_article_assignments table
    op.execute("""
        CREATE TABLE IF NOT EXISTS challenge_article_assignments (
            id SERIAL NOT NULL,
            user_challenge_response_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            article_id INTEGER NOT NULL,
            day_number INTEGER NOT NULL,
            assignment_date TIMESTAMP NOT NULL,
            opposition_strength FLOAT NOT NULL,
            match_algorithm VARCHAR(50) NOT NULL,
            match_reasoning VARCHAR(1000),
            is_sent BOOLEAN DEFAULT 'false' NOT NULL,
            sent_at TIMESTAMP,
            delivery_method VARCHAR(50) DEFAULT 'newsletter' NOT NULL,
            is_opened BOOLEAN DEFAULT 'false' NOT NULL,
            opened_at TIMESTAMP,
            is_clicked BOOLEAN DEFAULT 'false' NOT NULL,
            clicked_at TIMESTAMP,
            time_to_click_seconds INTEGER,
            quality_score FLOAT,
            user_feedback_helpful BOOLEAN,
            user_reported_inappropriate BOOLEAN DEFAULT 'false' NOT NULL,
            created_at TIMESTAMP DEFAULT now() NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(article_id) REFERENCES articles(id),
            FOREIGN KEY(user_challenge_response_id) REFERENCES user_challenge_responses(id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            CONSTRAINT uq_user_challenge_day UNIQUE (user_challenge_response_id, day_number),
            CONSTRAINT check_day_number_range CHECK (day_number >= 1 AND day_number <= 7)
        )
    """)

    # Create indexes for challenge_article_assignments
    op.execute("CREATE INDEX IF NOT EXISTS idx_user_challenge_assignments ON challenge_article_assignments (user_challenge_response_id, day_number)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_user_daily_assignment ON challenge_article_assignments (user_id, assignment_date)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_assignment_status ON challenge_article_assignments (is_sent, is_opened, is_clicked)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_article_assignments ON challenge_article_assignments (article_id, assignment_date)")

    # Create challenge_engagements table
    op.execute("""
        CREATE TABLE IF NOT EXISTS challenge_engagements (
            id SERIAL NOT NULL,
            user_id INTEGER NOT NULL,
            challenge_assignment_id INTEGER NOT NULL,
            engagement_type VARCHAR(50) NOT NULL,
            engagement_value VARCHAR(1000),
            engagement_time_seconds INTEGER,
            device_type VARCHAR(50),
            referrer VARCHAR(200),
            session_id VARCHAR(100),
            ip_address_hash VARCHAR(64),
            created_at TIMESTAMP DEFAULT now() NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(challenge_assignment_id) REFERENCES challenge_article_assignments(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Create indexes for challenge_engagements
    op.execute("CREATE INDEX IF NOT EXISTS idx_user_challenge_engagement ON challenge_engagements (user_id, challenge_assignment_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_engagement_type ON challenge_engagements (engagement_type, created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_engagement_timing ON challenge_engagements (created_at, engagement_time_seconds)")


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.execute("DROP TABLE IF EXISTS challenge_engagements CASCADE")
    op.execute("DROP TABLE IF EXISTS challenge_article_assignments CASCADE")
    op.execute("DROP TABLE IF EXISTS user_challenge_responses CASCADE")
    op.execute("DROP TABLE IF EXISTS challenge_claims CASCADE")
    op.execute("DROP TABLE IF EXISTS weekly_challenges CASCADE")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS challengeclaimtype")
    op.execute("DROP TYPE IF EXISTS challengeresponsestatus")
    op.execute("DROP TYPE IF EXISTS agreementlevel")

    # Remove challenge_participation_enabled from users table
    op.drop_column('users', 'challenge_participation_enabled')