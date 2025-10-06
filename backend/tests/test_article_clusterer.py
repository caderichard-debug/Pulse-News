"""
Tests for Article Clustering Service
"""
import pytest
from sqlmodel import Session, select
from ..app.models import (
    Article, Source, ArticleAnalysis, ArticleCluster, ArticleClusterMember,
    ProcessingStatus, PoliticalLean
)
from ..app.services.article_clusterer import (
    normalize_title,
    calculate_similarity,
    generate_cluster_hash,
    find_or_create_cluster,
    detect_similar_articles,
    cluster_article,
    get_cluster_comparison,
    get_article_cluster
)
from datetime import datetime, timedelta


class TestTitleNormalization:
    """Test title normalization"""

    def test_normalize_lowercase(self):
        """Test conversion to lowercase"""
        assert normalize_title("BREAKING NEWS") == "breaking news"

    def test_normalize_punctuation(self):
        """Test punctuation removal"""
        assert normalize_title("What's happening?!") == "whats happening"

    def test_normalize_whitespace(self):
        """Test whitespace normalization"""
        assert normalize_title("Too   many   spaces") == "too many spaces"

    def test_normalize_combined(self):
        """Test combined normalization"""
        result = normalize_title("Biden's Plan: What's Next?!")
        assert result == "bidens plan whats next"


class TestSimilarityCalculation:
    """Test similarity calculation"""

    def test_identical_titles(self):
        """Test identical titles give score of 1.0"""
        similarity = calculate_similarity(
            "Breaking News Today",
            "Breaking News Today"
        )
        assert similarity == 1.0

    def test_similar_titles(self):
        """Test similar titles give high score"""
        similarity = calculate_similarity(
            "Biden Announces Student Loan Forgiveness",
            "Biden Announces Student Debt Relief"
        )
        assert similarity > 0.6

    def test_different_titles(self):
        """Test different titles give low score"""
        similarity = calculate_similarity(
            "Weather Report for Monday",
            "Stock Market Crashes Today"
        )
        assert similarity < 0.4

    def test_with_summaries(self):
        """Test similarity with summaries included"""
        similarity = calculate_similarity(
            "Student Loans",
            "Student Debt",
            "Biden announces relief plan",
            "President unveils forgiveness program"
        )
        # Should be higher due to similar content
        assert similarity > 0.5


class TestClusterManagement:
    """Test cluster creation and management"""

    def test_generate_cluster_hash(self):
        """Test cluster hash generation"""
        hash1 = generate_cluster_hash("Student Loan Forgiveness")
        hash2 = generate_cluster_hash("Student Loan Forgiveness")
        hash3 = generate_cluster_hash("Different Topic")

        assert len(hash1) == 64  # SHA256 produces 64 hex chars
        assert hash1 == hash2  # Same topic = same hash
        assert hash1 != hash3  # Different topic = different hash

    def test_find_or_create_new_cluster(self, session: Session):
        """Test creating a new cluster"""
        cluster = find_or_create_cluster("Breaking News Topic", session)

        assert cluster.id is not None
        assert cluster.primary_topic == "Breaking News Topic"
        assert cluster.cluster_hash == generate_cluster_hash("Breaking News Topic")

    def test_find_existing_cluster(self, session: Session):
        """Test finding an existing cluster"""
        # Create first cluster
        cluster1 = find_or_create_cluster("Same Topic", session)
        session.commit()

        # Try to create again - should find existing
        cluster2 = find_or_create_cluster("Same Topic", session)

        assert cluster1.id == cluster2.id


class TestSimilarArticleDetection:
    """Test detecting similar articles"""

    def test_detect_similar_articles(self, session: Session):
        """Test finding similar articles within time window"""
        source = Source(
            name="News Source",
            url="https://news.com",
            rss_feed_url="https://news.com/feed"
        )
        session.add(source)
        session.commit()

        base_time = datetime.utcnow()

        # Create base article
        article1 = Article(
            source_id=source.id,
            title="Biden Announces Student Loan Forgiveness Plan",
            url="https://news.com/article1",
            published_at=base_time
        )
        session.add(article1)
        session.commit()

        analysis1 = ArticleAnalysis(
            article_id=article1.id,
            summary="President Biden announces relief for student loan borrowers",
            sentiment_score=5,
            political_lean=PoliticalLean.LEFT
        )
        session.add(analysis1)

        # Create similar article
        article2 = Article(
            source_id=source.id,
            title="Biden Unveils Student Debt Relief Program",
            url="https://news.com/article2",
            published_at=base_time + timedelta(hours=2)
        )
        session.add(article2)
        session.commit()

        analysis2 = ArticleAnalysis(
            article_id=article2.id,
            summary="The President unveils a plan to help student borrowers",
            sentiment_score=5,
            political_lean=PoliticalLean.LEFT
        )
        session.add(analysis2)

        # Create dissimilar article
        article3 = Article(
            source_id=source.id,
            title="Weather Forecast for Tuesday",
            url="https://news.com/article3",
            published_at=base_time + timedelta(hours=1)
        )
        session.add(article3)
        session.commit()

        analysis3 = ArticleAnalysis(
            article_id=article3.id,
            summary="Rain expected throughout the week",
            sentiment_score=0,
            political_lean=PoliticalLean.CENTER
        )
        session.add(analysis3)
        session.commit()

        # Detect similar articles
        similar = detect_similar_articles(article1, session, similarity_threshold=0.55)

        # Should find article2 but not article3
        assert len(similar) == 1
        assert similar[0][0].id == article2.id
        assert similar[0][1] > 0.55

    def test_time_window_filtering(self, session: Session):
        """Test that time window filters out old articles"""
        source = Source(
            name="News",
            url="https://news.com",
            rss_feed_url="https://news.com/feed"
        )
        session.add(source)
        session.commit()

        base_time = datetime.utcnow()

        # Recent article
        article1 = Article(
            source_id=source.id,
            title="Breaking News Story",
            url="https://news.com/recent",
            published_at=base_time
        )
        session.add(article1)
        session.commit()

        analysis1 = ArticleAnalysis(
            article_id=article1.id,
            summary="Recent news",
            sentiment_score=0,
            political_lean=PoliticalLean.CENTER
        )
        session.add(analysis1)

        # Old similar article (outside 72 hour window)
        article2 = Article(
            source_id=source.id,
            title="Breaking News Story",
            url="https://news.com/old",
            published_at=base_time - timedelta(hours=100)
        )
        session.add(article2)
        session.commit()

        analysis2 = ArticleAnalysis(
            article_id=article2.id,
            summary="Old news",
            sentiment_score=0,
            political_lean=PoliticalLean.CENTER
        )
        session.add(analysis2)
        session.commit()

        # Should not find old article
        similar = detect_similar_articles(article1, session, time_window_hours=72)
        assert len(similar) == 0


class TestArticleClustering:
    """Test clustering articles"""

    def test_cluster_similar_articles(self, session: Session):
        """Test clustering similar articles together"""
        source = Source(
            name="News",
            url="https://news.com",
            rss_feed_url="https://news.com/feed"
        )
        session.add(source)
        session.commit()

        base_time = datetime.utcnow()

        # Create similar articles
        articles = []
        for i in range(3):
            article = Article(
                source_id=source.id,
                title=f"Student Loan Forgiveness News {i}",
                url=f"https://news.com/article{i}",
                published_at=base_time + timedelta(hours=i)
            )
            session.add(article)
            session.commit()

            analysis = ArticleAnalysis(
                article_id=article.id,
                summary="Biden announces student debt relief program",
                sentiment_score=5,
                political_lean=PoliticalLean.LEFT
            )
            session.add(analysis)
            session.commit()

            articles.append(article)

        # Cluster the first article
        cluster = cluster_article(articles[0], session, similarity_threshold=0.6)
        session.commit()

        assert cluster is not None

        # Check all articles were added to cluster
        members = session.exec(
            select(ArticleClusterMember)
            .where(ArticleClusterMember.cluster_id == cluster.id)
        ).all()

        # Should have found and clustered similar articles
        assert len(members) >= 1

    def test_skip_already_clustered(self, session: Session):
        """Test that already clustered articles are skipped"""
        source = Source(
            name="News",
            url="https://news.com",
            rss_feed_url="https://news.com/feed"
        )
        session.add(source)
        session.commit()

        article = Article(
            source_id=source.id,
            title="Article",
            url="https://news.com/article",
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()

        # Create cluster and add article
        cluster = ArticleCluster(
            cluster_hash="test123",
            primary_topic="Test"
        )
        session.add(cluster)
        session.commit()

        member = ArticleClusterMember(
            cluster_id=cluster.id,
            article_id=article.id,
            similarity_score=1.0
        )
        session.add(member)
        session.commit()

        # Try to cluster again - should return None
        result = cluster_article(article, session)
        assert result is None


class TestClusterComparison:
    """Test cluster comparison generation"""

    def test_get_cluster_comparison(self, session: Session):
        """Test generating cross-source comparison"""
        source1 = Source(
            name="Reuters",
            url="https://reuters.com",
            rss_feed_url="https://reuters.com/feed",
            trust_score=9.5
        )
        source2 = Source(
            name="NPR",
            url="https://npr.org",
            rss_feed_url="https://npr.org/feed",
            trust_score=9.0
        )
        session.add_all([source1, source2])
        session.commit()

        # Create cluster
        cluster = ArticleCluster(
            cluster_hash="abc123",
            primary_topic="Student Loan Forgiveness"
        )
        session.add(cluster)
        session.commit()

        # Add articles from different sources
        base_time = datetime.utcnow()

        article1 = Article(
            source_id=source1.id,
            title="Biden Announces Forgiveness",
            url="https://reuters.com/article",
            published_at=base_time
        )
        session.add(article1)
        session.commit()

        analysis1 = ArticleAnalysis(
            article_id=article1.id,
            summary="Relief for borrowers",
            sentiment_score=5,
            political_lean=PoliticalLean.CENTER
        )
        session.add(analysis1)
        session.commit()

        article2 = Article(
            source_id=source2.id,
            title="Student Debt Relief Unveiled",
            url="https://npr.org/article",
            published_at=base_time
        )
        session.add(article2)
        session.commit()

        analysis2 = ArticleAnalysis(
            article_id=article2.id,
            summary="Biden helps students",
            sentiment_score=6,
            political_lean=PoliticalLean.LEFT
        )
        session.add(analysis2)
        session.commit()

        # Add to cluster
        member1 = ArticleClusterMember(
            cluster_id=cluster.id,
            article_id=article1.id,
            similarity_score=0.95
        )
        member2 = ArticleClusterMember(
            cluster_id=cluster.id,
            article_id=article2.id,
            similarity_score=0.90
        )
        session.add_all([member1, member2])
        session.commit()

        # Get comparison
        comparison = get_cluster_comparison(cluster.id, session)

        assert comparison is not None
        assert comparison["topic"] == "Student Loan Forgiveness"
        assert comparison["article_count"] == 2
        assert len(comparison["sources"]) == 2
        assert "Reuters" in comparison["sources"]
        assert "NPR" in comparison["sources"]
        assert len(comparison["articles"]) == 2

        # Check article data
        article_data = comparison["articles"][0]
        assert "article_id" in article_data
        assert "title" in article_data
        assert "source" in article_data
        assert "trust_score" in article_data
        assert "political_lean" in article_data
        assert "similarity" in article_data

    def test_get_article_cluster(self, session: Session):
        """Test getting cluster for a specific article"""
        source = Source(
            name="News",
            url="https://news.com",
            rss_feed_url="https://news.com/feed"
        )
        session.add(source)
        session.commit()

        cluster = ArticleCluster(
            cluster_hash="xyz789",
            primary_topic="Topic"
        )
        session.add(cluster)
        session.commit()

        article = Article(
            source_id=source.id,
            title="Article",
            url="https://news.com/article",
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()

        analysis = ArticleAnalysis(
            article_id=article.id,
            summary="Summary",
            sentiment_score=0,
            political_lean=PoliticalLean.CENTER
        )
        session.add(analysis)
        session.commit()

        member = ArticleClusterMember(
            cluster_id=cluster.id,
            article_id=article.id,
            similarity_score=1.0
        )
        session.add(member)
        session.commit()

        # Get cluster via article
        cluster_data = get_article_cluster(article.id, session)

        assert cluster_data is not None
        assert cluster_data["cluster_id"] == cluster.id
        assert cluster_data["topic"] == "Topic"

    def test_get_article_cluster_not_clustered(self, session: Session):
        """Test getting cluster for unclustered article"""
        source = Source(
            name="News",
            url="https://news.com",
            rss_feed_url="https://news.com/feed"
        )
        session.add(source)
        session.commit()

        article = Article(
            source_id=source.id,
            title="Article",
            url="https://news.com/article",
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()

        # Should return None
        cluster_data = get_article_cluster(article.id, session)
        assert cluster_data is None
