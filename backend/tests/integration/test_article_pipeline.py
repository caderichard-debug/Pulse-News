"""
Integration tests for the article processing pipeline:
RSS scrape -> content extraction -> AI analysis.

Status flow: PENDING (scraped) -> COMPLETED (content extracted) -> ArticleAnalysis row.
"""

import json
from datetime import datetime
from unittest.mock import Mock, patch

import feedparser
import pytest
from sqlmodel import Session, select

from app.models import Article, ArticleAnalysis, PoliticalLean, ProcessingStatus, Source
from app.services.ai_analyzer import analyze_articles_batch
from app.services.article_extractor import extract_article_content, process_pending_articles
from app.services.rss_scraper import scrape_source

LONG_CONTENT = "This is the full article content about AI development. " * 10


@pytest.fixture
def source(session: Session) -> Source:
    src = Source(
        name="TechNews",
        rss_feed_url="https://technews.example.com/feed",
        url="https://technews.example.com",
        is_active=True,
        trust_score=0.8,
    )
    session.add(src)
    session.commit()
    session.refresh(src)
    return src


def _feed(*entries):
    return feedparser.FeedParserDict(
        bozo=0,
        entries=[feedparser.FeedParserDict(e) for e in entries],
    )


def _completed_article(session, source, n, content="Some article content"):
    article = Article(
        title=f"Article {n}",
        url=f"https://technews.example.com/article-{n}",
        source_id=source.id,
        published_at=datetime(2025, 1, 1, 10, 0, 0),
        content_text=content,
        processing_status=ProcessingStatus.COMPLETED,
    )
    session.add(article)
    session.commit()
    session.refresh(article)
    return article


def _analysis(summary, sentiment=0, lean="center"):
    return {
        "summary": summary,
        "sentiment_score": sentiment,
        "political_lean": lean,
        "bias_indicators": "neutral",
        "key_stats": ["2% inflation reduction target"],
        "topic_category": "economics",
    }


class TestScrapeAndExtract:
    def test_scrape_then_extract(self, session: Session, source: Source):
        feed = _feed({"title": "New AI Development", "link": "https://technews.example.com/ai"})
        response = Mock(status_code=200, text="<html><body>ignored</body></html>")
        response.raise_for_status = Mock()

        with patch("app.services.rss_scraper.feedparser.parse", return_value=feed), \
             patch("app.services.article_extractor.requests.get", return_value=response), \
             patch("app.services.article_extractor.trafilatura.extract", return_value=LONG_CONTENT):
            scraped = scrape_source(source, session)
            assert len(scraped) == 1

            article = session.exec(select(Article).where(Article.source_id == source.id)).one()
            assert article.title == "New AI Development"
            assert article.processing_status == ProcessingStatus.PENDING

            processed = process_pending_articles(session, batch_size=5, delay=0)
            assert processed == 1

        session.refresh(article)
        assert article.processing_status == ProcessingStatus.COMPLETED
        assert "full article content" in article.content_text

    def test_rescrape_does_not_duplicate(self, session: Session, source: Source):
        feed = _feed({"title": "Same story", "link": "https://technews.example.com/same"})
        with patch("app.services.rss_scraper.feedparser.parse", return_value=feed):
            assert len(scrape_source(source, session)) == 1
            assert len(scrape_source(source, session)) == 0

    def test_bad_feed_and_network_errors_are_handled(self, session: Session, source: Source):
        bad_feed = feedparser.FeedParserDict(bozo=1, bozo_exception=Exception("Feed error"), entries=[])
        with patch("app.services.rss_scraper.feedparser.parse", return_value=bad_feed):
            assert scrape_source(source, session) == []

        import requests
        with patch("app.services.article_extractor.requests.get",
                   side_effect=requests.ConnectionError("Network error")), \
             patch("app.services.article_extractor.settings.http_backoff_base_seconds", 0):
            assert extract_article_content("https://technews.example.com/x")["success"] is False


class TestAnalysis:
    def _client(self, analyses):
        client = Mock()
        client.is_available.return_value = True
        client.analyze_articles_batch.return_value = analyses
        return client

    def test_analyzes_completed_articles(self, session: Session, source: Source):
        article = _completed_article(session, source, 1)
        client = self._client([_analysis("Government announces new economic policy")])

        with patch("app.services.ai_analyzer.openai_client", client):
            assert analyze_articles_batch(session, batch_size=5) == 1

        analysis = session.exec(
            select(ArticleAnalysis).where(ArticleAnalysis.article_id == article.id)
        ).one()
        assert "economic policy" in analysis.summary
        assert analysis.political_lean == PoliticalLean.CENTER
        # Stored as real JSON, not a Python repr
        assert json.loads(analysis.key_stats) == ["2% inflation reduction target"]

    def test_single_object_response_is_accepted(self, session: Session, source: Source):
        _completed_article(session, source, 1)
        client = self._client(_analysis("Only one"))

        with patch("app.services.ai_analyzer.openai_client", client):
            assert analyze_articles_batch(session, batch_size=5) == 1

    def test_batch_of_three(self, session: Session, source: Source):
        articles = [_completed_article(session, source, i) for i in range(3)]
        client = self._client([_analysis(f"Summary {i}", sentiment=i) for i in range(3)])

        with patch("app.services.ai_analyzer.openai_client", client):
            assert analyze_articles_batch(session, batch_size=3) == 3

        for i, article in enumerate(articles):
            analysis = session.exec(
                select(ArticleAnalysis).where(ArticleAnalysis.article_id == article.id)
            ).one()
            assert analysis.summary == f"Summary {i}"

    def test_count_mismatch_skips_batch(self, session: Session, source: Source):
        """If the model drops a result we can't tell which is which, so nothing is saved."""
        for i in range(3):
            _completed_article(session, source, i)
        client = self._client([_analysis("A"), _analysis("B")])

        with patch("app.services.ai_analyzer.openai_client", client):
            assert analyze_articles_batch(session, batch_size=3) == 0

        assert session.exec(select(ArticleAnalysis)).all() == []

    def test_skips_when_openai_unavailable(self, session: Session, source: Source):
        _completed_article(session, source, 1)
        client = Mock()
        client.is_available.return_value = False
        with patch("app.services.ai_analyzer.openai_client", client):
            assert analyze_articles_batch(session) == 0
