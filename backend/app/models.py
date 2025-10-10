from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import Enum as SQLEnum
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
    priority_level: int = Field(default=1, ge=1, le=5)  # 1-5 scale
    include_in_newsletter: bool = Field(default=True)
    articles_per_topic: int = Field(default=5)


class UserSourceSubscription(SQLModel, table=True):
    __tablename__ = "user_source_subscriptions"

    user_id: int = Field(foreign_key="users.id", primary_key=True)
    source_id: int = Field(foreign_key="sources.id", primary_key=True)
    subscribed: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Main Tables
class Source(SQLModel, table=True):
    __tablename__ = "sources"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200, index=True)
    url: str = Field(max_length=500)
    rss_feed_url: str = Field(max_length=500, unique=True)
    description: Optional[str] = Field(default=None, max_length=1000)
    trust_score: float = Field(default=0.8, ge=0.0, le=1.0)
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

    # Preferences
    source_discovery_mode: str = Field(default="some", max_length=20)  # 'none', 'some', 'open'
    article_order_preference: str = Field(default="mixed", max_length=20)  # 'good_first', 'good_last', 'mixed'
    articles_per_topic_default: int = Field(default=5)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None)

    # Relationships
    newsletters: List["Newsletter"] = Relationship(back_populates="user")


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
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ArticleCluster(SQLModel, table=True):
    __tablename__ = "article_clusters"

    id: Optional[int] = Field(default=None, primary_key=True)
    cluster_hash: str = Field(max_length=64, unique=True, index=True)
    primary_topic: str = Field(max_length=200, index=True)
    detected_at: datetime = Field(default_factory=datetime.utcnow)

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
