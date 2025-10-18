"""
Tests for source analyzer service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlmodel import Session, select

from app.models import Source, OrganizationalBias
from app.services.source_analyzer import SourceAnalyzer


class TestSourceAnalyzer:
    """Test suite for SourceAnalyzer service."""

    def test_analyze_source_bias_when_openai_unavailable(self, session: Session):
        """Test that analysis returns None when OpenAI is unavailable."""
        source = Source(
            name="Test Source",
            url="https://test.com",
            rss_feed_url="https://test.com/rss",
            trust_score=0.5
        )
        session.add(source)
        session.commit()

        analyzer = SourceAnalyzer(session)

        with patch('app.services.source_analyzer.openai_client') as mock_client:
            mock_client.is_available.return_value = False

            result = analyzer.analyze_source_bias(source)

            assert result is None

    def test_analyze_source_bias_when_already_set(self, session: Session):
        """Test that analysis returns existing bias when already set."""
        source = Source(
            name="Test Source",
            url="https://test.com",
            rss_feed_url="https://test.com/rss",
            trust_score=0.5,
            organizational_bias=OrganizationalBias.CENTER_LEFT,
            bias_description="Established center-left publication"
        )
        session.add(source)
        session.commit()

        analyzer = SourceAnalyzer(session)

        result = analyzer.analyze_source_bias(source)

        assert result is not None
        assert result["organizational_bias"] == OrganizationalBias.CENTER_LEFT
        assert result["bias_description"] == "Established center-left publication"
        assert result["confidence"] == 1.0

    def test_analyze_source_bias_success(self, session: Session):
        """Test successful source bias analysis."""
        source = Source(
            name="Progressive News Network",
            url="https://progressive-news.com",
            rss_feed_url="https://progressive-news.com/rss",
            trust_score=0.7
        )
        session.add(source)
        session.commit()

        analyzer = SourceAnalyzer(session)

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '''{
            "bias": "center-left",
            "description": "Progressive news outlet with center-left editorial stance",
            "confidence": 0.85
        }'''

        with patch('app.services.source_analyzer.openai_client') as mock_client:
            mock_client.is_available.return_value = True
            mock_client.client.chat.completions.create.return_value = mock_response
            mock_client.model_name = "gpt-4o-mini"

            result = analyzer.analyze_source_bias(
                source=source,
                article_title="Sample Article",
                article_content="Sample content"
            )

            assert result is not None
            assert result["organizational_bias"] == OrganizationalBias.CENTER_LEFT
            assert "Progressive news outlet" in result["bias_description"]
            assert result["confidence"] == 0.85

    def test_analyze_source_bias_all_bias_types(self, session: Session):
        """Test that all bias types are correctly mapped."""
        source = Source(
            name="Test Source",
            url="https://test.com",
            rss_feed_url="https://test.com/rss",
            trust_score=0.5
        )
        session.add(source)
        session.commit()

        analyzer = SourceAnalyzer(session)

        bias_mappings = [
            ("left", OrganizationalBias.LEFT),
            ("center-left", OrganizationalBias.CENTER_LEFT),
            ("center", OrganizationalBias.CENTER),
            ("center-right", OrganizationalBias.CENTER_RIGHT),
            ("right", OrganizationalBias.RIGHT),
        ]

        for bias_str, expected_enum in bias_mappings:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = f'''{{
                "bias": "{bias_str}",
                "description": "Test description",
                "confidence": 0.8
            }}'''

            with patch('app.services.source_analyzer.openai_client') as mock_client:
                mock_client.is_available.return_value = True
                mock_client.client.chat.completions.create.return_value = mock_response
                mock_client.model_name = "gpt-4o-mini"

                result = analyzer.analyze_source_bias(source)

                assert result is not None
                assert result["organizational_bias"] == expected_enum

    def test_update_source_with_bias(self, session: Session):
        """Test updating source with bias analysis."""
        source = Source(
            name="Test Source",
            url="https://test.com",
            rss_feed_url="https://test.com/rss",
            trust_score=0.5
        )
        session.add(source)
        session.commit()

        analyzer = SourceAnalyzer(session)

        bias_analysis = {
            "organizational_bias": OrganizationalBias.CENTER_RIGHT,
            "bias_description": "Conservative-leaning publication",
            "confidence": 0.75
        }

        updated_source = analyzer.update_source_with_bias(source, bias_analysis)

        assert updated_source.organizational_bias == OrganizationalBias.CENTER_RIGHT
        assert updated_source.bias_description == "Conservative-leaning publication"

        # Verify it's persisted
        session.refresh(source)
        assert source.organizational_bias == OrganizationalBias.CENTER_RIGHT
        assert source.bias_description == "Conservative-leaning publication"

    def test_analyze_source_bias_handles_errors(self, session: Session):
        """Test that analysis handles errors gracefully."""
        source = Source(
            name="Test Source",
            url="https://test.com",
            rss_feed_url="https://test.com/rss",
            trust_score=0.5
        )
        session.add(source)
        session.commit()

        analyzer = SourceAnalyzer(session)

        with patch('app.services.source_analyzer.openai_client') as mock_client:
            mock_client.is_available.return_value = True
            mock_client.client.chat.completions.create.side_effect = Exception("API Error")

            result = analyzer.analyze_source_bias(source)

            assert result is None

    def test_build_bias_analysis_prompt_with_article_content(self, session: Session):
        """Test prompt building with article content."""
        source = Source(
            name="Test Source",
            url="https://test.com",
            rss_feed_url="https://test.com/rss",
            trust_score=0.5
        )
        session.add(source)
        session.commit()

        analyzer = SourceAnalyzer(session)

        prompt = analyzer._build_bias_analysis_prompt(
            source_name="Test Source",
            domain="test.com",
            article_title="Test Article",
            article_content="This is test content for the article."
        )

        assert "Test Source" in prompt
        assert "test.com" in prompt
        assert "Test Article" in prompt
        assert "This is test content" in prompt
        assert "JSON format" in prompt

    def test_build_bias_analysis_prompt_without_article_content(self, session: Session):
        """Test prompt building without article content."""
        source = Source(
            name="Test Source",
            url="https://test.com",
            rss_feed_url="https://test.com/rss",
            trust_score=0.5
        )
        session.add(source)
        session.commit()

        analyzer = SourceAnalyzer(session)

        prompt = analyzer._build_bias_analysis_prompt(
            source_name="Test Source",
            domain="test.com"
        )

        assert "Test Source" in prompt
        assert "test.com" in prompt
        assert "Sample Article Title" not in prompt
        assert "Sample Article Content" not in prompt

    def test_map_bias_string_to_enum_unknown_defaults_to_center(self, session: Session):
        """Test that unknown bias strings default to CENTER."""
        source = Source(
            name="Test Source",
            url="https://test.com",
            rss_feed_url="https://test.com/rss",
            trust_score=0.5
        )
        session.add(source)
        session.commit()

        analyzer = SourceAnalyzer(session)

        result = analyzer._map_bias_string_to_enum("unknown-bias")

        assert result == OrganizationalBias.CENTER
