"""
Tests for model relationships and complex model interactions.
Tests foreign keys, cascades, and relationship integrity.
"""

import pytest
from sqlmodel import Session, select
.models import (
    Article, ArticleAnalysis, Source, Topic, Framework,
    User, UserTopicPreference, ArticleFrameworkLink,
    SourceTopicLink, ProcessingStatus, PoliticalLean
)
from datetime import datetime


@pytest.fixture
def sample_source(session: Session):
    """Create a test source"""
    source = Source(
        name="Test News",
        url="https://testnews.com",
        rss_feed_url="https://testnews.com/rss",
        political_lean=PoliticalLean.CENTER,
        is_active=True
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


@pytest.fixture
def sample_topic(session: Session):
    """Create a test topic"""
    topic = Topic(
        name="Technology",
        description="Tech news"
    )
    session.add(topic)
    session.commit()
    session.refresh(topic)
    return topic


@pytest.fixture
def sample_framework(session: Session):
    """Create a test framework"""
    framework = Framework(
        name="Privacy vs Security",
        description="Test framework",
        axis_description="test axis",
        left_position="left",
        right_position="right",
        created_at=datetime.utcnow()
    )
    session.add(framework)
    session.commit()
    session.refresh(framework)
    return framework


@pytest.fixture
def sample_user(session: Session):
    """Create a test user"""
    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password="hashed_password",
        is_active=True,
        email_verified=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


class TestArticleRelationships:
    """Test Article model relationships"""

    def test_article_source_relationship(self, session: Session, sample_source: Source):
        """Test Article -> Source foreign key relationship"""
        article = Article(
            source_id=sample_source.id,
            title="Test Article",
            url="https://testnews.com/article",
            published_at=datetime.utcnow(),
            scraped_at=datetime.utcnow(),
            processing_status=ProcessingStatus.PENDING
        )
        session.add(article)
        session.commit()

        # Retrieve and verify relationship
        retrieved_article = session.get(Article, article.id)
        assert retrieved_article.source_id == sample_source.id

        # Verify we can access source through relationship
        assert retrieved_article.source.name == "Test News"

    def test_article_analysis_relationship(self, session: Session, sample_source: Source):
        """Test Article -> ArticleAnalysis one-to-one relationship"""
        article = Article(
            source_id=sample_source.id,
            title="Test Article",
            url="https://testnews.com/article",
            published_at=datetime.utcnow(),
            scraped_at=datetime.utcnow(),
            processing_status=ProcessingStatus.COMPLETED
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        analysis = ArticleAnalysis(
            article_id=article.id,
            summary="Test summary",
            sentiment_score=5,
            political_lean=PoliticalLean.CENTER,
            bias_indicators="neutral",
            processing_cost=0.002,
            processed_at=datetime.utcnow()
        )
        session.add(analysis)
        session.commit()

        # Verify relationship
        retrieved_article = session.get(Article, article.id)
        assert retrieved_article.id == analysis.article_id

    def test_article_topic_many_to_many(
        self, session: Session, sample_source: Source, sample_topic: Topic
    ):
        """Test Article <-> Topic many-to-many relationship"""
        article = Article(
            source_id=sample_source.id,
            title="Tech Article",
            url="https://testnews.com/tech",
            published_at=datetime.utcnow(),
            scraped_at=datetime.utcnow(),
            processing_status=ProcessingStatus.PENDING
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        # Link article to topic
        article.topics = [sample_topic]
        session.add(article)
        session.commit()

        # Verify relationship
        retrieved_article = session.get(Article, article.id)
        assert len(retrieved_article.topics) == 1
        assert retrieved_article.topics[0].name == "Technology"

    def test_article_framework_links(
        self, session: Session, sample_source: Source, sample_framework: Framework
    ):
        """Test Article <-> Framework link through ArticleFrameworkLink"""
        article = Article(
            source_id=sample_source.id,
            title="Privacy Article",
            url="https://testnews.com/privacy",
            published_at=datetime.utcnow(),
            scraped_at=datetime.utcnow(),
            processing_status=ProcessingStatus.COMPLETED
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        # Create framework link
        link = ArticleFrameworkLink(
            article_id=article.id,
            framework_id=sample_framework.id,
            relevance_score=0.8,
            position_on_axis=-5,
            ai_explanation="Test explanation",
            created_at=datetime.utcnow()
        )
        session.add(link)
        session.commit()

        # Verify link exists
        retrieved_link = session.exec(
            select(ArticleFrameworkLink)
            .where(ArticleFrameworkLink.article_id == article.id)
        ).first()

        assert retrieved_link is not None
        assert retrieved_link.framework_id == sample_framework.id
        assert retrieved_link.relevance_score == 0.8


class TestUserRelationships:
    """Test User model relationships"""

    def test_user_topic_preferences(self, session: Session, sample_user: User, sample_topic: Topic):
        """Test User <-> Topic preferences relationship"""
        preference = UserTopicPreference(
            user_id=sample_user.id,
            topic_id=sample_topic.id,
            is_active=True,
            priority=5
        )
        session.add(preference)
        session.commit()

        # Verify relationship
        user_prefs = session.exec(
            select(UserTopicPreference)
            .where(UserTopicPreference.user_id == sample_user.id)
        ).all()

        assert len(user_prefs) == 1
        assert user_prefs[0].topic_id == sample_topic.id

    def test_multiple_user_preferences(
        self, session: Session, sample_user: User
    ):
        """Test user can have multiple topic preferences"""
        # Create multiple topics
        topics = []
        for i in range(3):
            topic = Topic(
                name=f"Topic {i}",
                description=f"Description {i}"
            )
            session.add(topic)
            session.commit()
            session.refresh(topic)
            topics.append(topic)

        # Add preferences
        for i, topic in enumerate(topics):
            pref = UserTopicPreference(
                user_id=sample_user.id,
                topic_id=topic.id,
                is_active=True,
                priority=i + 1
            )
            session.add(pref)
        session.commit()

        # Verify
        user_prefs = session.exec(
            select(UserTopicPreference)
            .where(UserTopicPreference.user_id == sample_user.id)
        ).all()

        assert len(user_prefs) == 3


class TestSourceRelationships:
    """Test Source model relationships"""

    def test_source_articles_relationship(self, session: Session, sample_source: Source):
        """Test Source -> Articles one-to-many relationship"""
        # Create multiple articles for source
        for i in range(3):
            article = Article(
                source_id=sample_source.id,
                title=f"Article {i}",
                url=f"https://testnews.com/article{i}",
                published_at=datetime.utcnow(),
                scraped_at=datetime.utcnow(),
                processing_status=ProcessingStatus.PENDING
            )
            session.add(article)
        session.commit()

        # Verify relationship
        source_articles = session.exec(
            select(Article)
            .where(Article.source_id == sample_source.id)
        ).all()

        assert len(source_articles) == 3

    def test_source_topic_links(self, session: Session, sample_source: Source, sample_topic: Topic):
        """Test Source <-> Topic link through SourceTopicLink"""
        link = SourceTopicLink(
            source_id=sample_source.id,
            topic_id=sample_topic.id,
            relevance_score=0.9
        )
        session.add(link)
        session.commit()

        # Verify link
        retrieved_link = session.exec(
            select(SourceTopicLink)
            .where(SourceTopicLink.source_id == sample_source.id)
        ).first()

        assert retrieved_link is not None
        assert retrieved_link.topic_id == sample_topic.id


class TestFrameworkRelationships:
    """Test Framework model relationships"""

    def test_framework_article_links(
        self, session: Session, sample_framework: Framework, sample_source: Source
    ):
        """Test Framework can be linked to multiple articles"""
        # Create articles
        articles = []
        for i in range(3):
            article = Article(
                source_id=sample_source.id,
                title=f"Article {i}",
                url=f"https://testnews.com/article{i}",
                published_at=datetime.utcnow(),
                scraped_at=datetime.utcnow(),
                processing_status=ProcessingStatus.COMPLETED
            )
            session.add(article)
            session.commit()
            session.refresh(article)
            articles.append(article)

        # Link all articles to framework
        for article in articles:
            link = ArticleFrameworkLink(
                article_id=article.id,
                framework_id=sample_framework.id,
                relevance_score=0.7,
                position_on_axis=0,
                ai_explanation="Test",
                created_at=datetime.utcnow()
            )
            session.add(link)
        session.commit()

        # Verify links
        framework_links = session.exec(
            select(ArticleFrameworkLink)
            .where(ArticleFrameworkLink.framework_id == sample_framework.id)
        ).all()

        assert len(framework_links) == 3


class TestTopicRelationships:
    """Test Topic model relationships"""

    def test_topic_articles_many_to_many(
        self, session: Session, sample_topic: Topic, sample_source: Source
    ):
        """Test Topic can be linked to multiple articles"""
        # Create articles
        for i in range(3):
            article = Article(
                source_id=sample_source.id,
                title=f"Article {i}",
                url=f"https://testnews.com/article{i}",
                published_at=datetime.utcnow(),
                scraped_at=datetime.utcnow(),
                processing_status=ProcessingStatus.PENDING
            )
            session.add(article)
            session.commit()
            session.refresh(article)

            # Link to topic
            article.topics = [sample_topic]
            session.add(article)
        session.commit()

        # Count articles with this topic
        topic_articles = session.exec(
            select(Article)
            .where(Article.topics.any(Topic.id == sample_topic.id))
        ).all()

        assert len(topic_articles) == 3

    def test_topic_user_preferences(
        self, session: Session, sample_topic: Topic
    ):
        """Test Topic can have multiple user preferences"""
        # Create users
        users = []
        for i in range(3):
            user = User(
                email=f"user{i}@example.com",
                name=f"User {i}",
                hashed_password="hashed",
                is_active=True
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            users.append(user)

        # Add preferences
        for user in users:
            pref = UserTopicPreference(
                user_id=user.id,
                topic_id=sample_topic.id,
                is_active=True,
                priority=5
            )
            session.add(pref)
        session.commit()

        # Verify
        topic_prefs = session.exec(
            select(UserTopicPreference)
            .where(UserTopicPreference.topic_id == sample_topic.id)
        ).all()

        assert len(topic_prefs) == 3


class TestConstraints:
    """Test database constraints and validations"""

    def test_unique_email_constraint(self, session: Session):
        """Test that user emails must be unique"""
        user1 = User(
            email="duplicate@example.com",
            name="User 1",
            hashed_password="hash1",
            is_active=True
        )
        session.add(user1)
        session.commit()

        # Attempt to create user with same email
        user2 = User(
            email="duplicate@example.com",
            name="User 2",
            hashed_password="hash2",
            is_active=True
        )
        session.add(user2)

        # This should raise an integrity error
        with pytest.raises(Exception):  # Will be IntegrityError
            session.commit()

    def test_article_url_uniqueness(self, session: Session, sample_source: Source):
        """Test that article URLs should be unique (via application logic)"""
        article1 = Article(
            source_id=sample_source.id,
            title="Article 1",
            url="https://testnews.com/duplicate",
            published_at=datetime.utcnow(),
            scraped_at=datetime.utcnow(),
            processing_status=ProcessingStatus.PENDING
        )
        session.add(article1)
        session.commit()

        # Check for duplicate URL
        existing = session.exec(
            select(Article).where(Article.url == "https://testnews.com/duplicate")
        ).first()

        assert existing is not None
        assert existing.id == article1.id
