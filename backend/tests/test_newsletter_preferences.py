"""
Tests for newsletter service with user preferences.
Run with: pytest backend/tests/test_newsletter_preferences.py -v
"""

import pytest
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from ..app.models import (
    User, Source, Article, ArticleAnalysis, Topic, UserTopicPreference,
    UserSourceSubscription, PoliticalLean
)
from ..app.services.newsletter_service import _generate_newsletter_for_user
from ..app.utils.auth import hash_password
from datetime import datetime


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # Create sources
        source1 = Source(
            id=1,
            name="Reuters",
            url="https://reuters.com",
            rss_feed_url="https://reuters.com/rss",
            trust_score=0.95
        )
        source2 = Source(
            id=2,
            name="NPR",
            url="https://npr.org",
            rss_feed_url="https://npr.org/rss",
            trust_score=0.90
        )
        source3 = Source(
            id=3,
            name="Fox News",
            url="https://foxnews.com",
            rss_feed_url="https://foxnews.com/rss",
            trust_score=0.65
        )
        session.add_all([source1, source2, source3])

        # Create topics
        topic1 = Topic(id=1, name="Politics", description="Political news")
        topic2 = Topic(id=2, name="Tech", description="Technology news")
        session.add_all([topic1, topic2])

        # Create test user with specific preferences
        user = User(
            id=1,
            email="testuser@example.com",
            hashed_password=hash_password("testpass123"),
            email_verified=True,
            is_active=True,
            source_discovery_mode="some",
            article_order_preference="mixed",
            articles_per_topic_default=5
        )
        session.add(user)

        # Create articles with different sources and sentiments
        articles_data = [
            (1, 1, "Good News from Reuters", 8),  # positive sentiment
            (2, 1, "Neutral News from Reuters", 0),
            (3, 2, "Good News from NPR", 7),  # positive sentiment
            (4, 2, "Bad News from NPR", -5),  # negative sentiment
            (5, 3, "Bad News from Fox", -8),  # negative sentiment
            (6, 3, "Neutral from Fox", 1),
        ]

        for article_id, source_id, title, sentiment in articles_data:
            article = Article(
                id=article_id,
                source_id=source_id,
                title=title,
                url=f"https://example.com/{article_id}",
                published_at=datetime.utcnow(),
                processing_status="completed"
            )
            session.add(article)

            analysis = ArticleAnalysis(
                article_id=article_id,
                summary=f"Summary for {title}",
                sentiment_score=sentiment,
                political_lean=PoliticalLean.CENTER
            )
            session.add(analysis)

        session.commit()
        yield session


class TestNewsletterSourceFiltering:
    """Tests for source-based filtering in newsletter"""

    def test_newsletter_includes_all_sources_when_no_subscriptions(self, session: Session):
        """Test that newsletter includes all sources when user has no subscriptions"""
        user = session.get(User, 1)

        # Add topic preference
        pref = UserTopicPreference(
            user_id=1,
            topic_id=1,
            priority_level=5,
            include_in_newsletter=True,
            articles_per_topic=5
        )
        session.add(pref)
        session.commit()

        result = _generate_newsletter_for_user(user, session)

        assert result is not None
        # Should include articles from all sources
        assert len(result["article_ids"]) > 0

    def test_newsletter_filters_by_subscribed_sources(self, session: Session):
        """Test that newsletter only includes articles from subscribed sources"""
        user = session.get(User, 1)

        # Subscribe only to Reuters (source 1)
        sub = UserSourceSubscription(user_id=1, source_id=1, subscribed=True)
        session.add(sub)

        # Add topic preference
        pref = UserTopicPreference(
            user_id=1,
            topic_id=1,
            priority_level=5,
            include_in_newsletter=True,
            articles_per_topic=5
        )
        session.add(pref)
        session.commit()

        result = _generate_newsletter_for_user(user, session)

        assert result is not None

        # Get the articles
        from sqlmodel import select
        article_ids = result["article_ids"]
        articles = session.exec(
            select(Article).where(Article.id.in_(article_ids))
        ).all()

        # All articles should be from Reuters (source 1)
        assert all(article.source_id == 1 for article in articles)

    def test_newsletter_filters_multiple_subscribed_sources(self, session: Session):
        """Test that newsletter includes articles from multiple subscribed sources"""
        user = session.get(User, 1)

        # Subscribe to Reuters and NPR (sources 1 and 2)
        sub1 = UserSourceSubscription(user_id=1, source_id=1, subscribed=True)
        sub2 = UserSourceSubscription(user_id=1, source_id=2, subscribed=True)
        session.add_all([sub1, sub2])

        # Add topic preference
        pref = UserTopicPreference(
            user_id=1,
            topic_id=1,
            priority_level=5,
            include_in_newsletter=True,
            articles_per_topic=5
        )
        session.add(pref)
        session.commit()

        result = _generate_newsletter_for_user(user, session)

        assert result is not None

        # Get the articles
        from sqlmodel import select
        article_ids = result["article_ids"]
        articles = session.exec(
            select(Article).where(Article.id.in_(article_ids))
        ).all()

        # Articles should only be from Reuters or NPR (sources 1 and 2)
        source_ids = {article.source_id for article in articles}
        assert source_ids.issubset({1, 2})


class TestNewsletterArticleOrdering:
    """Tests for article ordering based on user preferences"""

    def test_newsletter_orders_good_news_first(self, session: Session):
        """Test that articles are ordered by positive sentiment first"""
        user = session.get(User, 1)
        user.article_order_preference = "good_first"
        session.add(user)

        # Add topic preference
        pref = UserTopicPreference(
            user_id=1,
            topic_id=1,
            priority_level=5,
            include_in_newsletter=True,
            articles_per_topic=10  # Get all articles
        )
        session.add(pref)
        session.commit()

        result = _generate_newsletter_for_user(user, session)

        assert result is not None

        # Get articles with their sentiment scores, preserving order
        from sqlmodel import select
        article_ids = result["article_ids"]

        # Create a mapping of article_id -> sentiment_score
        articles_map = {}
        articles_with_analysis = session.exec(
            select(Article, ArticleAnalysis)
            .join(ArticleAnalysis)
            .where(Article.id.in_(article_ids))
        ).all()

        for article, analysis in articles_with_analysis:
            articles_map[article.id] = analysis.sentiment_score

        # Extract sentiments in the order they appear in article_ids
        sentiments = [articles_map[aid] for aid in article_ids]

        # Should be in descending order (positive first)
        assert sentiments == sorted(sentiments, reverse=True)

    def test_newsletter_orders_good_news_last(self, session: Session):
        """Test that articles are ordered by negative sentiment first"""
        user = session.get(User, 1)
        user.article_order_preference = "good_last"
        session.add(user)

        # Add topic preference
        pref = UserTopicPreference(
            user_id=1,
            topic_id=1,
            priority_level=5,
            include_in_newsletter=True,
            articles_per_topic=10
        )
        session.add(pref)
        session.commit()

        result = _generate_newsletter_for_user(user, session)

        assert result is not None

        # Get articles with their sentiment scores, preserving order
        from sqlmodel import select
        article_ids = result["article_ids"]

        # Create a mapping of article_id -> sentiment_score
        articles_map = {}
        articles_with_analysis = session.exec(
            select(Article, ArticleAnalysis)
            .join(ArticleAnalysis)
            .where(Article.id.in_(article_ids))
        ).all()

        for article, analysis in articles_with_analysis:
            articles_map[article.id] = analysis.sentiment_score

        # Extract sentiments in the order they appear in article_ids
        sentiments = [articles_map[aid] for aid in article_ids]

        # Should be in ascending order (negative first)
        assert sentiments == sorted(sentiments)

    def test_newsletter_mixed_ordering_is_random(self, session: Session):
        """Test that 'mixed' ordering doesn't follow sentiment pattern"""
        user = session.get(User, 1)
        user.article_order_preference = "mixed"
        session.add(user)

        # Add topic preference
        pref = UserTopicPreference(
            user_id=1,
            topic_id=1,
            priority_level=5,
            include_in_newsletter=True,
            articles_per_topic=10
        )
        session.add(pref)
        session.commit()

        result = _generate_newsletter_for_user(user, session)

        assert result is not None

        # Get articles with their sentiment scores
        from sqlmodel import select
        article_ids = result["article_ids"]
        articles_with_analysis = session.exec(
            select(Article, ArticleAnalysis)
            .join(ArticleAnalysis)
            .where(Article.id.in_(article_ids))
        ).all()

        # Extract sentiment scores
        sentiments = [analysis.sentiment_score for _, analysis in articles_with_analysis]

        # Should NOT be strictly ascending or descending
        # (This test might occasionally fail due to randomness, but unlikely)
        is_ascending = sentiments == sorted(sentiments)
        is_descending = sentiments == sorted(sentiments, reverse=True)

        # For truly random, it's unlikely to be perfectly sorted
        # We'll accept this if there are enough articles
        if len(sentiments) > 3:
            assert not (is_ascending or is_descending), "Mixed order should not be strictly sorted"


class TestNewsletterArticlesPerTopic:
    """Tests for articles_per_topic_default setting"""

    def test_newsletter_respects_articles_per_topic_limit(self, session: Session):
        """Test that newsletter limits articles based on user preference"""
        user = session.get(User, 1)
        user.articles_per_topic_default = 2  # Only 2 articles per topic
        session.add(user)

        # Subscribe to one topic
        pref = UserTopicPreference(
            user_id=1,
            topic_id=1,
            priority_level=5,
            include_in_newsletter=True,
            articles_per_topic=2
        )
        session.add(pref)
        session.commit()

        result = _generate_newsletter_for_user(user, session)

        assert result is not None

        # Should have at most 2 articles (1 topic * 2 articles)
        assert len(result["article_ids"]) <= 2

    def test_newsletter_scales_with_multiple_topics(self, session: Session):
        """Test that total articles scale with number of topics"""
        user = session.get(User, 1)
        user.articles_per_topic_default = 3
        session.add(user)

        # Subscribe to 2 topics
        pref1 = UserTopicPreference(
            user_id=1,
            topic_id=1,
            priority_level=5,
            include_in_newsletter=True,
            articles_per_topic=3
        )
        pref2 = UserTopicPreference(
            user_id=1,
            topic_id=2,
            priority_level=5,
            include_in_newsletter=True,
            articles_per_topic=3
        )
        session.add_all([pref1, pref2])
        session.commit()

        result = _generate_newsletter_for_user(user, session)

        assert result is not None

        # Should have at most 6 articles (2 topics * 3 articles)
        assert len(result["article_ids"]) <= 6


class TestNewsletterCombinedPreferences:
    """Tests for combined source filtering + ordering + article count"""

    def test_newsletter_applies_all_preferences(self, session: Session):
        """Test that all user preferences are applied together"""
        user = session.get(User, 1)
        user.articles_per_topic_default = 3
        user.article_order_preference = "good_first"
        session.add(user)

        # Subscribe only to NPR and Reuters
        sub1 = UserSourceSubscription(user_id=1, source_id=1, subscribed=True)
        sub2 = UserSourceSubscription(user_id=1, source_id=2, subscribed=True)
        session.add_all([sub1, sub2])

        # Subscribe to one topic
        pref = UserTopicPreference(
            user_id=1,
            topic_id=1,
            priority_level=5,
            include_in_newsletter=True,
            articles_per_topic=3
        )
        session.add(pref)
        session.commit()

        result = _generate_newsletter_for_user(user, session)

        assert result is not None

        # Get articles
        from sqlmodel import select
        article_ids = result["article_ids"]
        articles_with_analysis = session.exec(
            select(Article, ArticleAnalysis)
            .join(ArticleAnalysis)
            .where(Article.id.in_(article_ids))
        ).all()

        # 1. Check article count (should be <= 3)
        assert len(articles_with_analysis) <= 3

        # 2. Check source filtering (should only be from Reuters or NPR)
        source_ids = {article.source_id for article, _ in articles_with_analysis}
        assert source_ids.issubset({1, 2})

        # 3. Check ordering (good news first - descending sentiment)
        # Create mapping to preserve order
        articles_map = {article.id: analysis.sentiment_score for article, analysis in articles_with_analysis}
        sentiments = [articles_map[aid] for aid in article_ids]
        assert sentiments == sorted(sentiments, reverse=True)
