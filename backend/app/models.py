from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import Enum as SQLEnum, UniqueConstraint, Index
from typing import Optional, List
from datetime import datetime
from enum import Enum


# Enums
class ProcessingStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PoliticalLean(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class OrganizationalBias(str, Enum):
    LEFT = "left"
    CENTER_LEFT = "center-left"
    CENTER = "center"
    CENTER_RIGHT = "center-right"
    RIGHT = "right"


class SubscriptionTier(str, Enum):
    FREE = "FREE"
    PREMIUM = "PREMIUM"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    DISPUTED = "disputed"
    FALSE = "false"


class VerificationMethod(str, Enum):
    CROSS_REFERENCE = "cross_reference"
    API_CHECK = "api_check"
    MANUAL = "manual"
    AI_ANALYSIS = "ai_analysis"


# Challenge System Enums
class ChallengeClaimType(str, Enum):
    POLICY = "policy"
    SOCIAL_ISSUE = "social_issue"
    ECONOMIC = "economic"
    TECHNOLOGY = "technology"
    ENVIRONMENT = "environment"
    FOREIGN_POLICY = "foreign_policy"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"


class ChallengeResponseStatus(str, Enum):
    PENDING = "pending"
    RESPONDED = "responded"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class AgreementLevel(str, Enum):
    STRONGLY_DISAGREE = "strongly_disagree"
    DISAGREE = "disagree"
    NEUTRAL = "neutral"
    AGREE = "agree"
    STRONGLY_AGREE = "strongly_agree"


# Link Tables (Many-to-Many relationships)
class SourceTopicLink(SQLModel, table=True):
    __tablename__ = "source_topics"

    source_id: int = Field(foreign_key="sources.id", primary_key=True)
    topic_id: int = Field(foreign_key="topics.id", primary_key=True)


class ArticleTopicLink(SQLModel, table=True):
    __tablename__ = "article_topics"

    article_id: int = Field(foreign_key="articles.id", primary_key=True)
    topic_id: int = Field(foreign_key="topics.id", primary_key=True)


class NewsletterArticle(SQLModel, table=True):
    __tablename__ = "newsletter_articles"

    newsletter_id: int = Field(foreign_key="newsletters.id", primary_key=True)
    article_id: int = Field(foreign_key="articles.id", primary_key=True)
    display_order: int = Field(default=0)


class ArticleFrameworkLink(SQLModel, table=True):
    __tablename__ = "article_frameworks"
    __table_args__ = (
        UniqueConstraint('article_id', 'framework_id', name='uq_article_framework'),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="articles.id", index=True)
    framework_id: int = Field(foreign_key="frameworks.id", index=True)
    relevance_score: float = Field(ge=0.0, le=1.0)  # 0-1 scale
    position_on_axis: int = Field(ge=-10, le=10)  # -10 (left) to +10 (right)
    ai_explanation: str = Field(max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserTopicPreference(SQLModel, table=True):
    __tablename__ = "user_topic_preferences"

    user_id: int = Field(foreign_key="users.id", primary_key=True)
    topic_id: int = Field(foreign_key="topics.id", primary_key=True)
    include_in_newsletter: bool = Field(default=True)
    articles_per_topic: int = Field(default=5)


class UserSourceSubscription(SQLModel, table=True):
    __tablename__ = "user_source_subscriptions"

    user_id: int = Field(foreign_key="users.id", primary_key=True)
    source_id: int = Field(foreign_key="sources.id", primary_key=True)
    subscribed: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ArticleFavorite(SQLModel, table=True):
    """User's favorited articles for later reading."""
    __tablename__ = "article_favorites"

    user_id: int = Field(foreign_key="users.id", primary_key=True)
    article_id: int = Field(foreign_key="articles.id", primary_key=True)
    favorited_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = Field(default=None, max_length=500)

    __table_args__ = (
        Index("idx_user_favorites", "user_id", "favorited_at"),
        Index("idx_article_favorites", "article_id"),
    )


# Main Tables
class Source(SQLModel, table=True):
    __tablename__ = "sources"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200, index=True)
    url: str = Field(max_length=500)
    rss_feed_url: str = Field(max_length=500, unique=True)
    description: Optional[str] = Field(default=None, max_length=1000)
    trust_score: float = Field(default=0.8, ge=0.0, le=1.0)

    # Organizational bias
    organizational_bias: Optional[OrganizationalBias] = Field(
        default=None,
        sa_column=Column(SQLEnum(OrganizationalBias, values_callable=lambda x: [e.value for e in x]), nullable=True)
    )
    bias_description: Optional[str] = Field(default=None, max_length=500)

    # Curator recommendation flag
    is_recommended: bool = Field(default=False, index=True)

    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    articles: List["Article"] = Relationship(back_populates="source")
    topics: List["Topic"] = Relationship(
        back_populates="sources",
        link_model=SourceTopicLink
    )


class Topic(SQLModel, table=True):
    __tablename__ = "topics"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active_default: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    sources: List["Source"] = Relationship(
        back_populates="topics",
        link_model=SourceTopicLink
    )
    articles: List["Article"] = Relationship(
        back_populates="topics",
        link_model=ArticleTopicLink
    )


class Article(SQLModel, table=True):
    __tablename__ = "articles"

    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="sources.id", index=True)

    # Article metadata
    title: str = Field(max_length=500, index=True)
    url: str = Field(max_length=1000, unique=True, index=True)
    author: Optional[str] = Field(default=None, max_length=200)
    published_at: datetime = Field(index=True)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    # Content
    content_text: Optional[str] = Field(default=None)  # Full article text
    word_count: Optional[int] = Field(default=None)
    extraction_method: Optional[str] = Field(default=None, max_length=50)  # trafilatura, readability, etc.

    # Topic categorization
    topic_category: Optional[str] = Field(default=None, max_length=100, index=True)

    # Processing status
    processing_status: ProcessingStatus = Field(
        default=ProcessingStatus.PENDING,
        sa_column=Column(
            SQLEnum(ProcessingStatus, values_callable=lambda x: [e.value for e in x]),
            index=True
        )
    )
    processed_at: Optional[datetime] = Field(default=None)

    # User submission tracking
    is_user_submitted: bool = Field(default=False, index=True)
    submitted_by_user_id: Optional[int] = Field(default=None, foreign_key="users.id")

    # Relationships
    source: Optional["Source"] = Relationship(back_populates="articles")
    analysis: Optional["ArticleAnalysis"] = Relationship(back_populates="article")
    frameworks: List["Framework"] = Relationship(
        back_populates="articles",
        link_model=ArticleFrameworkLink
    )
    topics: List["Topic"] = Relationship(
        back_populates="articles",
        link_model=ArticleTopicLink
    )
    challenge_assignments: List["ChallengeArticleAssignment"] = Relationship(back_populates="article")
    challenge_claims: List["ChallengeClaim"] = Relationship(back_populates="source_article")


class ArticleAnalysis(SQLModel, table=True):
    __tablename__ = "article_analysis"

    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="articles.id", unique=True, index=True)

    # AI-generated analysis
    summary: str = Field(max_length=1000)  # 100-150 word summary
    sentiment_score: int = Field(ge=-10, le=10)  # -10 (negative) to +10 (positive)
    political_lean: PoliticalLean = Field(
        sa_column=Column(SQLEnum(PoliticalLean, values_callable=lambda x: [e.value for e in x]))
    )
    bias_indicators: Optional[str] = Field(default=None, max_length=500)

    # Statistics extraction
    key_stats: Optional[str] = Field(default=None)  # JSON string of extracted stats
    stats_verified: Optional[bool] = Field(default=None)
    stats_verification_status: VerificationStatus = Field(
        default=VerificationStatus.UNVERIFIED,
        sa_column=Column(SQLEnum(VerificationStatus, values_callable=lambda x: [e.value for e in x]))
    )
    stats_verification_date: Optional[datetime] = Field(default=None)

    # Context generation
    has_context: bool = Field(default=False)

    # Processing metadata
    processing_cost: Optional[float] = Field(default=None)  # Track API costs
    tokens_used: Optional[int] = Field(default=None)
    processed_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    article: Optional["Article"] = Relationship(back_populates="analysis")


class Framework(SQLModel, table=True):
    __tablename__ = "frameworks"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Framework definition
    name: str = Field(max_length=200, unique=True, index=True)
    description: str = Field(max_length=1000)

    # Axis definition (the debate spectrum)
    axis_description: str = Field(max_length=200)  # e.g., "individual freedom �� collective welfare"
    left_position: str = Field(max_length=200)  # e.g., "Maximize individual autonomy"
    right_position: str = Field(max_length=200)  # e.g., "Prioritize community benefit"

    # Metadata
    article_count: int = Field(default=0)  # How many articles relate to this
    last_active: datetime = Field(default_factory=datetime.utcnow, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_seed: bool = Field(default=False)  # True if hand-curated, False if AI-generated

    # Relationships
    articles: List["Article"] = Relationship(
        back_populates="frameworks",
        link_model=ArticleFrameworkLink
    )


class PasswordResetToken(SQLModel, table=True):
    __tablename__ = "password_reset_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    token: str = Field(max_length=255, unique=True, index=True)
    expires_at: datetime = Field(index=True)
    used: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    user: Optional["User"] = Relationship(back_populates="password_reset_tokens")


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(max_length=255, unique=True, index=True)
    email_verified: bool = Field(default=False)
    hashed_password: str = Field(max_length=255)
    name: Optional[str] = Field(default=None, max_length=200)

    # Subscription
    subscription_tier: SubscriptionTier = Field(
        default=SubscriptionTier.FREE,
        sa_column=Column(SQLEnum(SubscriptionTier, values_callable=lambda x: [e.value for e in x]))
    )
    is_active: bool = Field(default=True)

    # Admin fields
    is_admin: bool = Field(default=False)
    admin_notes: Optional[str] = Field(default=None, max_length=1000)
    last_admin_action: Optional[datetime] = Field(default=None)

    # Preferences
    source_discovery_mode: str = Field(default="some", max_length=20)  # 'none', 'some', 'open'
    article_order_preference: str = Field(default="mixed", max_length=20)  # 'good_first', 'good_last', 'mixed'
    articles_per_topic_default: int = Field(default=5)
    theme_preference: str = Field(default="auto", max_length=10)  # 'light', 'dark', or 'auto'
    newsletter_enabled: bool = Field(default=True)  # Whether user wants to receive newsletters
    challenge_participation_enabled: bool = Field(default=True)  # Whether user wants to receive weekly challenges

    # OAuth authentication fields
    oauth_provider: Optional[str] = Field(default=None, max_length=50)  # 'google', 'apple'
    oauth_provider_id: Optional[str] = Field(default=None, max_length=255)  # Provider-specific user ID
    oauth_provider_data: Optional[str] = Field(default=None, max_length=2000)  # JSON string with provider data
    oauth_avatar_url: Optional[str] = Field(default=None, max_length=500)
    passwordless_login_enabled: bool = Field(default=False)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None)

    # Relationships
    newsletters: List["Newsletter"] = Relationship(back_populates="user")
    password_reset_tokens: List["PasswordResetToken"] = Relationship(back_populates="user")
    oauth_accounts: List["OAuthAccount"] = Relationship(back_populates="user")

    # Challenge system relationships
    challenge_responses: List["UserChallengeResponse"] = Relationship(back_populates="user")
    challenge_assignments: List["ChallengeArticleAssignment"] = Relationship(back_populates="user")
    challenge_engagement: List["ChallengeEngagement"] = Relationship(back_populates="user")


class OAuthAccount(SQLModel, table=True):
    """OAuth account linking and token management for users."""
    __tablename__ = "oauth_accounts"
    __table_args__ = (
        Index("idx_oauth_user_provider", "user_id", "provider"),
        Index("idx_oauth_provider_user", "provider", "provider_user_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    provider: str = Field(max_length=50)  # 'google', 'apple'
    provider_user_id: str = Field(max_length=255)  # Provider-specific user ID
    provider_data: Optional[str] = Field(default=None, max_length=2000)  # JSON string with provider data
    access_token: Optional[str] = Field(default=None, max_length=1000)
    refresh_token: Optional[str] = Field(default=None, max_length=1000)
    token_expires_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: Optional["User"] = Relationship(back_populates="oauth_accounts")




class Newsletter(SQLModel, table=True):
    __tablename__ = "newsletters"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)

    # Email metadata
    subject: str = Field(max_length=200)
    html_content: str = Field(default="")  # Email HTML content
    sent_at: Optional[datetime] = Field(default=None, index=True)

    # Content references (JSON arrays of IDs)
    article_ids: str = Field(max_length=500, default="[]")  # e.g., "[1,2,3,4,5]"
    framework_ids: str = Field(max_length=500, default="[]")  # e.g., "[1,2,3]"

    # Tracking
    email_opened: bool = Field(default=False)
    links_clicked: int = Field(default=0)

    # Relationships
    user: Optional["User"] = Relationship(back_populates="newsletters")


# New Enhancement Tables

class StatisticVerification(SQLModel, table=True):
    __tablename__ = "statistic_verifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="articles.id", index=True)

    # Statistic details
    statistic_text: str = Field(max_length=500)
    context: Optional[str] = Field(default=None, max_length=1000)
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.UNVERIFIED,
        sa_column=Column(SQLEnum(VerificationStatus, values_callable=lambda x: [e.value for e in x]))
    )
    verification_method: Optional[VerificationMethod] = Field(
        default=None,
        sa_column=Column(SQLEnum(VerificationMethod, values_callable=lambda x: [e.value for e in x]))
    )
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    # V2: Source Tracing
    source_url: Optional[str] = Field(default=None, max_length=500)
    source_name: Optional[str] = Field(default=None, max_length=200)
    source_excerpt: Optional[str] = Field(default=None, max_length=1000)
    source_credibility_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    # V2: Fact-Checking
    fact_check_status: Optional[str] = Field(default=None, max_length=50)
    fact_check_source: Optional[str] = Field(default=None, max_length=100)
    fact_check_url: Optional[str] = Field(default=None, max_length=500)
    fact_check_details: Optional[str] = Field(default=None, max_length=2000)

    # Metadata
    verified_at: Optional[datetime] = Field(default=None)
    last_checked: Optional[datetime] = Field(default=None)
    verification_notes: Optional[str] = Field(default=None, max_length=500)  # Failure reasons or additional info
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ArticleCluster(SQLModel, table=True):
    __tablename__ = "article_clusters"

    id: Optional[int] = Field(default=None, primary_key=True)
    cluster_hash: str = Field(max_length=64, unique=True, index=True)
    primary_topic: str = Field(max_length=200, index=True)
    detected_at: datetime = Field(default_factory=datetime.utcnow)

    # Event-specific fields
    event_signature: str = Field(max_length=500, index=True)  # Unique event identifier
    event_date: Optional[datetime] = Field(default=None, index=True)  # When the event occurred
    article_count: int = Field(default=0)  # Number of articles in cluster
    sources_count: int = Field(default=0)  # Number of unique sources
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    members: List["ArticleClusterMember"] = Relationship(back_populates="cluster")


class ArticleClusterMember(SQLModel, table=True):
    __tablename__ = "article_cluster_members"

    cluster_id: int = Field(foreign_key="article_clusters.id", primary_key=True)
    article_id: int = Field(foreign_key="articles.id", primary_key=True)
    similarity_score: float = Field(ge=0.0, le=1.0)

    # Relationships
    cluster: Optional["ArticleCluster"] = Relationship(back_populates="members")


class ArticleContext(SQLModel, table=True):
    __tablename__ = "article_context"

    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="articles.id", unique=True, index=True)

    # Context components
    background: Optional[str] = Field(default=None, max_length=2000)
    key_players: Optional[str] = Field(default=None)  # JSON array of strings
    timeline: Optional[str] = Field(default=None)  # JSON array of timeline events
    significance: Optional[str] = Field(default=None, max_length=1000)
    next_developments: Optional[str] = Field(default=None, max_length=1000)

    # Sources and quality
    sources_consulted: Optional[str] = Field(default=None)  # JSON array of URLs
    context_quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    tokens_used: Optional[int] = Field(default=None)


class SourceCredibilityRating(SQLModel, table=True):
    __tablename__ = "source_credibility_ratings"

    id: Optional[int] = Field(default=None, primary_key=True)
    domain: str = Field(unique=True, index=True, max_length=200)
    credibility_score: float = Field(ge=0.0, le=1.0)

    # Credibility factors
    is_academic: bool = Field(default=False)
    is_government: bool = Field(default=False)
    is_news_organization: bool = Field(default=False)
    is_think_tank: bool = Field(default=False)

    # Metadata
    rating_method: str = Field(max_length=100)  # manual, ai, mbfc_api, etc.
    notes: Optional[str] = Field(default=None, max_length=1000)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JobExecutionHistory(SQLModel, table=True):
    """Track all background job executions for monitoring and debugging."""
    __tablename__ = "job_execution_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(max_length=100, index=True)
    job_name: str = Field(max_length=200)

    # Execution details
    started_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    completed_at: Optional[datetime] = Field(default=None)
    duration_seconds: Optional[float] = Field(default=None)

    # Status
    status: str = Field(max_length=20)  # success, failed, running
    result_data: Optional[str] = Field(default=None)  # JSON string
    error_message: Optional[str] = Field(default=None, max_length=2000)

    # Metrics
    items_processed: Optional[int] = Field(default=None)
    api_calls_made: Optional[int] = Field(default=None)
    tokens_used: Optional[int] = Field(default=None)

    # Trigger info
    triggered_by: str = Field(default="scheduler")  # scheduler, admin, api
    triggered_by_user_id: Optional[int] = Field(default=None)


class AdminAuditLog(SQLModel, table=True):
    """Track all admin actions for security and debugging."""
    __tablename__ = "admin_audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(foreign_key="users.id", index=True)
    admin_email: str = Field(max_length=255, index=True)

    # Action details
    action_type: str = Field(max_length=100, index=True)
    resource_type: str = Field(max_length=100)
    resource_id: Optional[str] = Field(default=None, max_length=100)

    # Change tracking
    old_value: Optional[str] = Field(default=None)  # JSON string
    new_value: Optional[str] = Field(default=None)  # JSON string

    # Metadata
    ip_address: Optional[str] = Field(default=None, max_length=50)
    user_agent: Optional[str] = Field(default=None, max_length=500)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    notes: Optional[str] = Field(default=None, max_length=500)


class ViewpointRelationship(SQLModel, table=True):
    __tablename__ = "viewpoint_relationships"

    id: Optional[int] = Field(default=None, primary_key=True)
    primary_article_id: int = Field(foreign_key="articles.id")
    opposing_article_id: int = Field(foreign_key="articles.id")

    # Relationship type and strength
    relationship_type: str = Field(max_length=50)  # "source_bias", "framework_opposition", "sentiment_contrast", "temporal_evolution"
    opposition_strength: float = Field(ge=0.0, le=1.0)  # How different they are

    # AI-generated explanation
    ai_explanation: Optional[str] = Field(default=None, max_length=500)

    # Framework analysis details (for framework_opposition relationships)
    framework_name: Optional[str] = Field(default=None, max_length=100)  # Name of the framework
    reasoning: Optional[str] = Field(default=None, max_length=500)  # Detailed reasoning for the relationship
    primary_position: Optional[int] = Field(default=None)  # Primary article's position on framework
    opposing_position: Optional[int] = Field(default=None)  # Opposing article's position on framework

    # Enhanced analyzer explanations (for framework_opposition relationships)
    how_this_opposes: Optional[str] = Field(default=None, max_length=1000)  # How this article opposes the primary (mechanism-focused)
    why_this_opposes: Optional[str] = Field(default=None, max_length=1000)  # Why this opposition matters (reasoning-focused)

    # Quality and engagement tracking
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)  # AI assessment of relationship quality
    user_engagement_count: int = Field(default=0)  # How many users clicked this
    user_feedback_helpful: int = Field(default=0)  # Helpful feedback count
    user_feedback_not_helpful: int = Field(default=0)  # Not helpful feedback count

    # Generation metadata
    generation_method: str = Field(max_length=50, default="automatic")  # "automatic", "batch", "manual"
    ai_model_version: Optional[str] = Field(default=None, max_length=50)  # Track which AI model generated this
    processing_time_ms: Optional[int] = Field(default=None)  # Track generation performance

    # Status and lifecycle
    is_active: bool = Field(default=True, index=True)  # Soft delete capability
    last_regenerated: Optional[datetime] = Field(default=None)  # For periodic regeneration
    expires_at: Optional[datetime] = Field(default=None)  # When to refresh this relationship

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        Index("idx_primary_article", "primary_article_id"),
        Index("idx_opposing_article", "opposing_article_id"),
        Index("idx_relationship_type", "relationship_type"),
        Index("idx_active_relationships", "is_active", "created_at"),
        Index("idx_strength_order", "opposition_strength", "created_at"),
        Index("idx_expiration", "expires_at", "is_active"),
    )


# ============================================================================
# CHALLENGE SYSTEM MODELS
# ============================================================================

class WeeklyChallenge(SQLModel, table=True):
    """Weekly challenge set with 4 ethical claims for users to consider."""
    __tablename__ = "weekly_challenges"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Challenge identification
    week_start_date: datetime = Field(index=True)  # Monday of challenge week
    week_end_date: datetime = Field(index=True)  # Sunday of challenge week
    challenge_date: datetime = Field(index=True)  # Friday when challenge is delivered
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=500)

    # Generation and admin controls
    generation_method: str = Field(max_length=50, default="automatic")  # automatic, manual, batch
    ai_model_version: Optional[str] = Field(default=None, max_length=50)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    is_published: bool = Field(default=False, index=True)  # Ready for delivery
    published_at: Optional[datetime] = Field(default=None)

    # Admin review fields
    admin_notes: Optional[str] = Field(default=None, max_length=1000)
    last_reviewed_by: Optional[int] = Field(default=None, foreign_key="users.id")
    last_reviewed_at: Optional[datetime] = Field(default=None)

    # Participation tracking
    total_participants: int = Field(default=0)  # How many users received this challenge
    is_active: bool = Field(default=True)  # For soft delete/archiving

    # Relationships
    claims: List["ChallengeClaim"] = Relationship(back_populates="weekly_challenge")
    user_responses: List["UserChallengeResponse"] = Relationship(back_populates="weekly_challenge")


class ChallengeClaim(SQLModel, table=True):
    """Individual ethical claim within a weekly challenge."""
    __tablename__ = "challenge_claims"

    id: Optional[int] = Field(default=None, primary_key=True)
    weekly_challenge_id: int = Field(foreign_key="weekly_challenges.id", index=True)

    # Claim content
    claim_text: str = Field(max_length=300)  # The ethical claim statement
    claim_type: ChallengeClaimType = Field(
        sa_column=Column(SQLEnum(ChallengeClaimType, values_callable=lambda x: [e.value for e in x]))
    )

    # Background information
    background_context: Optional[str] = Field(default=None, max_length=1000)
    key_statistics: Optional[str] = Field(default=None, max_length=1000)
    political_lean_distribution: Optional[str] = Field(default=None, max_length=200)

    # AI analysis of claim properties
    controversy_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    reasonableness_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    # Source tracking
    source_article_id: Optional[int] = Field(default=None, foreign_key="articles.id")
    source_topic_ids: Optional[str] = Field(default=None)  # Comma-separated topic IDs

    # Display and ordering
    display_order: int = Field(default=0)
    is_active: bool = Field(default=True)

    # Generation metadata
    generation_method: str = Field(max_length=50, default="automatic")
    ai_prompt_used: Optional[str] = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    weekly_challenge: Optional[WeeklyChallenge] = Relationship(back_populates="claims")
    user_responses: List["UserChallengeResponse"] = Relationship(back_populates="selected_claim")
    source_article: Optional[Article] = Relationship(back_populates="challenge_claims")


class UserChallengeResponse(SQLModel, table=True):
    """User's response to a weekly challenge."""
    __tablename__ = "user_challenge_responses"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    weekly_challenge_id: int = Field(foreign_key="weekly_challenges.id", index=True)
    selected_claim_id: int = Field(foreign_key="challenge_claims.id", index=True)

    # User's response
    agreement_level: AgreementLevel = Field(
        sa_column=Column(SQLEnum(AgreementLevel, values_callable=lambda x: [e.value for e in x]))
    )

    # Response timing and metadata
    response_time_seconds: Optional[int] = Field(default=None)  # Time to complete form
    status: ChallengeResponseStatus = Field(
        default=ChallengeResponseStatus.PENDING,
        sa_column=Column(SQLEnum(ChallengeResponseStatus, values_callable=lambda x: [e.value for e in x]), index=True)
    )
    responded_at: Optional[datetime] = Field(default=None)  # When user submitted response
    response_source: str = Field(max_length=50, default="newsletter")  # newsletter, web_form, api

    # Challenge timing
    challenge_started_at: Optional[datetime] = Field(default=None)  # When 7-day article delivery started
    challenge_completed_at: Optional[datetime] = Field(default=None)  # When all 7 articles delivered

    # Article engagement tracking
    articles_sent_count: int = Field(default=0)  # How many challenge articles sent (0-7)
    articles_engaged_count: int = Field(default=0)  # How many articles user opened/clicked

    # User feedback
    found_valuable: Optional[bool] = Field(default=None)  # Did user find challenge valuable
    feedback_text: Optional[str] = Field(default=None, max_length=1000)  # User comments
    opted_out_future: bool = Field(default=False)  # Opt out of future challenges

    # Relationships
    user: Optional["User"] = Relationship(back_populates="challenge_responses")
    weekly_challenge: Optional[WeeklyChallenge] = Relationship(back_populates="user_responses")
    selected_claim: Optional[ChallengeClaim] = Relationship(back_populates="user_responses")
    article_assignments: List["ChallengeArticleAssignment"] = Relationship(back_populates="user_response")


class ChallengeArticleAssignment(SQLModel, table=True):
    """Daily challenge article assigned to a user."""
    __tablename__ = "challenge_article_assignments"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_challenge_response_id: int = Field(foreign_key="user_challenge_responses.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    article_id: int = Field(foreign_key="articles.id", index=True)

    # Assignment details
    day_number: int = Field(ge=1, le=7)  # Day 1-7 of challenge
    assignment_date: datetime = Field(index=True)  # When this article should be sent

    # Matching algorithm details
    opposition_strength: float = Field(ge=0.0, le=1.0)  # How strongly this opposes user's stance
    match_algorithm: str = Field(max_length=50)  # database, web_search, historical
    match_reasoning: Optional[str] = Field(default=None, max_length=1000)  # Why this article was selected
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    # Delivery tracking
    is_sent: bool = Field(default=False)  # Whether article has been sent
    sent_at: Optional[datetime] = Field(default=None)
    delivery_method: str = Field(max_length=50, default="newsletter")  # newsletter, email, push

    # Engagement tracking
    is_opened: bool = Field(default=False)  # Whether user opened the article
    opened_at: Optional[datetime] = Field(default=None)
    is_clicked: bool = Field(default=False)  # Whether user clicked to read full article
    clicked_at: Optional[datetime] = Field(default=None)
    time_to_click_seconds: Optional[int] = Field(default=None)  # Time from send to click

    # User feedback
    user_feedback_helpful: Optional[bool] = Field(default=None)
    user_reported_inappropriate: bool = Field(default=False)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user_response: Optional[UserChallengeResponse] = Relationship(back_populates="article_assignments")
    user: Optional["User"] = Relationship(back_populates="challenge_assignments")
    article: Optional[Article] = Relationship(back_populates="challenge_assignments")
    engagement_events: List["ChallengeEngagement"] = Relationship(back_populates="challenge_assignment")


class ChallengeEngagement(SQLModel, table=True):
    """Analytics tracking for challenge system engagement."""
    __tablename__ = "challenge_engagements"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    challenge_assignment_id: int = Field(foreign_key="challenge_article_assignments.id", index=True)

    # Engagement details
    engagement_type: str = Field(max_length=50)  # open, click, share, feedback, etc.
    engagement_value: Optional[str] = Field(default=None, max_length=1000)  # JSON or specific value
    engagement_time_seconds: Optional[int] = Field(default=None)  # Time spent on engagement

    # User context
    device_type: Optional[str] = Field(default=None, max_length=50)  # mobile, desktop, tablet
    referrer: Optional[str] = Field(default=None, max_length=200)  # Source of engagement
    session_id: Optional[str] = Field(default=None, max_length=100)  # User session
    ip_address_hash: Optional[str] = Field(default=None, max_length=64)  # Anonymized IP

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: Optional["User"] = Relationship(back_populates="challenge_engagement")
    challenge_assignment: Optional[ChallengeArticleAssignment] = Relationship(back_populates="engagement_events")
