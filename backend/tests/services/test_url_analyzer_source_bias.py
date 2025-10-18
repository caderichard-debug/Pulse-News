"""
Tests for source bias analysis in URL analyzer.
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlmodel import Session
from datetime import datetime

from app.models import Source, Article, OrganizationalBias
from app.services.url_analyzer import URLAnalyzer


class TestURLAnalyzerSourceBias:
    """Test suite for source bias analysis in URLAnalyzer."""

    def test_format_response_includes_source_bias(self, session: Session):
        """Test that _format_response includes source bias fields."""
        # Create source with bias
        source = Source(
            name="Test News",
            url="https://test-news.com",
            rss_feed_url="https://test-news.com/rss",
            trust_score=0.8,
            organizational_bias=OrganizationalBias.CENTER_LEFT,
            bias_description="Center-left news organization"
        )
        session.add(source)
        session.commit()
        session.refresh(source)

        # Create article
        article = Article(
            title="Test Article",
            url="https://test-news.com/article",
            content_text="Article content",
            source_id=source.id,
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        analyzer = URLAnalyzer(session)
        response = analyzer._format_response(article)

        # Verify source bias is included
        assert response["source"] is not None
        assert response["source"]["organizational_bias"] == "center-left"
        assert response["source"]["bias_description"] == "Center-left news organization"

    def test_format_response_with_no_source_bias(self, session: Session):
        """Test that _format_response handles sources without bias."""
        # Create source without bias
        source = Source(
            name="Test News",
            url="https://test-news.com",
            rss_feed_url="https://test-news.com/rss",
            trust_score=0.8
        )
        session.add(source)
        session.commit()
        session.refresh(source)

        # Create article
        article = Article(
            title="Test Article",
            url="https://test-news2.com/article",
            content_text="Article content",
            source_id=source.id,
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        analyzer = URLAnalyzer(session)
        response = analyzer._format_response(article)

        # Verify source bias fields are None
        assert response["source"] is not None
        assert response["source"]["organizational_bias"] is None
        assert response["source"]["bias_description"] is None

    def test_analyze_url_calls_source_analyzer_for_new_source(self, session: Session):
        """Test that analyze_url calls source analyzer for new sources."""
        test_url = "https://new-source.com/article"

        # Mock extraction
        mock_extraction = {
            "success": True,
            "title": "Test Article",
            "content": "Article content",
            "author": "Author",
            "published_date": datetime.utcnow(),
            "site_name": "New Source",
            "method": "trafilatura",
            "word_count": 50
        }

        # Mock bias analysis
        mock_bias_response = MagicMock()
        mock_bias_response.choices[0].message.content = '''{
            "bias": "right",
            "description": "Conservative publication",
            "confidence": 0.9
        }'''

        analyzer = URLAnalyzer(session)

        with patch('app.services.url_analyzer.extract_article_content') as mock_extract, \
             patch('app.services.url_analyzer.openai_client') as mock_openai, \
             patch('app.services.source_analyzer.openai_client') as mock_bias_openai, \
             patch.object(analyzer, '_validate_url') as mock_validate:

            mock_validate.return_value = None
            mock_extract.return_value = mock_extraction

            # Mock AI analysis
            mock_openai.is_available.return_value = True
            mock_openai.analyze_articles_batch.return_value = [
                {
                    "summary": "Test summary",
                    "sentiment_score": 2,
                    "political_lean": "right"
                }
            ]

            # Mock source bias analysis
            mock_bias_openai.is_available.return_value = True
            mock_bias_openai.client.chat.completions.create.return_value = mock_bias_response
            mock_bias_openai.model_name = "gpt-4o-mini"

            # Perform analysis (sync wrapper for async)
            import asyncio
            result = asyncio.run(analyzer.analyze_url(test_url))

            # Verify source was created with bias
            assert result["source"] is not None
            assert result["source"]["organizational_bias"] == "right"
            assert result["source"]["bias_description"] == "Conservative publication"

            # Verify source exists in database with bias
            from sqlmodel import select
            source = session.exec(
                select(Source).where(Source.url == "https://new-source.com")
            ).first()

            assert source is not None
            assert source.organizational_bias == OrganizationalBias.RIGHT
            assert source.bias_description == "Conservative publication"

    def test_analyze_url_skips_bias_for_existing_source_with_bias(self, session: Session):
        """Test that analyze_url doesn't re-analyze sources that already have bias."""
        # Create source with existing bias
        source = Source(
            name="Existing Source",
            url="https://existing.com",
            rss_feed_url="https://existing.com/rss",
            trust_score=0.7,
            organizational_bias=OrganizationalBias.CENTER,
            bias_description="Balanced coverage"
        )
        session.add(source)
        session.commit()

        test_url = "https://existing.com/new-article"

        mock_extraction = {
            "success": True,
            "title": "New Article",
            "content": "New content",
            "author": "Author",
            "published_date": datetime.utcnow(),
            "site_name": "Existing Source",
            "method": "trafilatura",
            "word_count": 100
        }

        analyzer = URLAnalyzer(session)

        with patch('app.services.url_analyzer.extract_article_content') as mock_extract, \
             patch('app.services.url_analyzer.openai_client') as mock_openai, \
             patch('app.services.source_analyzer.openai_client') as mock_bias_openai, \
             patch.object(analyzer, '_validate_url') as mock_validate:

            mock_validate.return_value = None
            mock_extract.return_value = mock_extraction

            mock_openai.is_available.return_value = True
            mock_openai.analyze_articles_batch.return_value = [
                {
                    "summary": "Summary",
                    "sentiment_score": 0,
                    "political_lean": "center"
                }
            ]

            mock_bias_openai.is_available.return_value = True

            # Perform analysis
            import asyncio
            result = asyncio.run(analyzer.analyze_url(test_url))

            # Verify source bias remains unchanged
            assert result["source"]["organizational_bias"] == "center"
            assert result["source"]["bias_description"] == "Balanced coverage"

            # Verify bias analysis was NOT called (used existing bias)
            mock_bias_openai.client.chat.completions.create.assert_not_called()
