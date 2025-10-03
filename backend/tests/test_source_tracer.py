"""
Tests for Source Tracer Service
"""
import pytest
from unittest.mock import Mock, patch
from sqlmodel import Session
from app.services.source_tracer import SourceTracer, get_source_tracer


class TestSourceTracer:
    """Test source tracing functionality"""

    @patch('app.services.source_tracer.openai_api')
    def test_ai_extract_source_success(self, mock_openai_api):
        """Test successful AI source extraction"""
        tracer = SourceTracer()

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='''
        {
            "source_url": "https://bls.gov/data",
            "source_name": "Bureau of Labor Statistics",
            "source_excerpt": "According to the Bureau of Labor Statistics...",
            "confidence": 0.9
        }
        '''))]
        mock_openai_api.chat.completions.create.return_value = mock_response

        result = tracer._ai_extract_source(
            statistic_text="3.5% unemployment",
            article_content="According to the Bureau of Labor Statistics, unemployment is 3.5%",
            article_url="https://test.com/article"
        )

        assert result is not None
        assert result["source_url"] == "https://bls.gov/data"
        assert result["source_name"] == "Bureau of Labor Statistics"
        assert result["confidence"] == 0.9

    @patch('app.services.source_tracer.openai_api')
    def test_ai_extract_source_with_markdown_code_block(self, mock_openai_api):
        """Test AI extraction when response is wrapped in markdown code block"""
        tracer = SourceTracer()

        # Mock OpenAI response with markdown wrapper
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='''```json
        {
            "source_url": "https://cdc.gov/study",
            "source_name": "CDC",
            "source_excerpt": "The CDC reports...",
            "confidence": 0.85
        }
        ```'''))]
        mock_openai_api.chat.completions.create.return_value = mock_response

        result = tracer._ai_extract_source(
            statistic_text="50% increase",
            article_content="The CDC reports a 50% increase",
            article_url="https://test.com/article"
        )

        assert result is not None
        assert result["source_name"] == "CDC"

    @patch('app.services.source_tracer.openai_api')
    def test_ai_extract_source_no_source_found(self, mock_openai_api):
        """Test AI extraction when no source is found"""
        tracer = SourceTracer()

        # Mock OpenAI response with null values
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='''
        {
            "source_url": null,
            "source_name": null,
            "source_excerpt": "No source mentioned",
            "confidence": 0.0
        }
        '''))]
        mock_openai_api.chat.completions.create.return_value = mock_response

        result = tracer._ai_extract_source(
            statistic_text="99%",
            article_content="Some article without source",
            article_url="https://test.com/article"
        )

        assert result is not None
        assert result["source_url"] is None
        assert result["source_name"] is None

    @patch('app.services.source_tracer.openai_api')
    def test_ai_extract_source_invalid_json(self, mock_openai_api):
        """Test AI extraction with invalid JSON response"""
        tracer = SourceTracer()

        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='Invalid JSON response'))]
        mock_openai_api.chat.completions.create.return_value = mock_response

        result = tracer._ai_extract_source(
            statistic_text="test",
            article_content="content",
            article_url="https://test.com"
        )

        assert result is None

    def test_extract_nearby_urls_success(self):
        """Test extracting URLs near a statistic"""
        tracer = SourceTracer()

        article_content = """
        According to a recent study (https://research.org/study123), unemployment fell to 3.5%.
        This data was also confirmed by https://bls.gov/data.
        """

        urls = tracer._extract_nearby_urls("3.5%", article_content)

        assert len(urls) > 0
        assert "https://research.org/study123" in urls or "https://bls.gov/data" in urls

    def test_extract_nearby_urls_filters_social_media(self):
        """Test that social media URLs are filtered out"""
        tracer = SourceTracer()

        article_content = """
        The statistic is 50%. Share on https://twitter.com/share or https://facebook.com/share.
        Source: https://cdc.gov/data
        """

        urls = tracer._extract_nearby_urls("50%", article_content)

        # Should filter out twitter/facebook
        assert not any("twitter.com" in url for url in urls)
        assert not any("facebook.com" in url for url in urls)
        # Should keep CDC
        if urls:
            assert any("cdc.gov" in url for url in urls)

    def test_extract_nearby_urls_no_match(self):
        """Test URL extraction when statistic not found"""
        tracer = SourceTracer()

        urls = tracer._extract_nearby_urls(
            "99.9%",
            "Article without this statistic"
        )

        assert urls == []

    @patch('app.services.source_tracer.openai_api')
    def test_trace_statistic_source_full_pipeline(self, mock_openai_api):
        """Test full source tracing pipeline"""
        tracer = SourceTracer()

        # Mock AI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='''
        {
            "source_url": "https://nih.gov/study",
            "source_name": "National Institutes of Health",
            "source_excerpt": "NIH study shows...",
            "confidence": 0.88
        }
        '''))]
        mock_openai_api.chat.completions.create.return_value = mock_response

        result = tracer.trace_statistic_source(
            statistic_text="50% effectiveness",
            article_content="The NIH study shows 50% effectiveness. https://nih.gov/study",
            article_url="https://news.com/article",
            session=None
        )

        assert result is not None
        assert result["source_name"] == "National Institutes of Health"
        assert result["source_url"] == "https://nih.gov/study"

    @patch('app.services.source_tracer.openai_api')
    def test_trace_statistic_source_ai_fails_uses_nearby_url(self, mock_openai_api):
        """Test that nearby URLs are used when AI fails to find source"""
        tracer = SourceTracer()

        # Mock AI response with no URL
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='''
        {
            "source_url": null,
            "source_name": "Some Source",
            "source_excerpt": "...",
            "confidence": 0.5
        }
        '''))]
        mock_openai_api.chat.completions.create.return_value = mock_response

        article_with_url = "The study (https://research.org/data) found 75% success rate."

        result = tracer.trace_statistic_source(
            statistic_text="75%",
            article_content=article_with_url,
            article_url="https://news.com/article",
            session=None
        )

        # Should use nearby URL
        assert result is not None
        assert result["source_url"] == "https://research.org/data"
        # Confidence should be lowered
        assert result["confidence"] <= 0.6

    def test_get_source_tracer_singleton(self):
        """Test singleton pattern"""
        tracer1 = get_source_tracer()
        tracer2 = get_source_tracer()

        assert tracer1 is tracer2

    @patch('app.services.source_tracer.openai_api', None)
    def test_ai_extract_source_no_api_key(self):
        """Test that extraction fails gracefully without API key"""
        tracer = SourceTracer()

        result = tracer._ai_extract_source(
            statistic_text="test",
            article_content="content",
            article_url="https://test.com"
        )

        assert result is None

    @patch('app.services.source_tracer.openai_api')
    def test_ai_extract_source_truncates_long_content(self, mock_openai_api):
        """Test that long article content is truncated"""
        tracer = SourceTracer()

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"source_url": null, "source_name": null, "confidence": 0.0}'))]
        mock_openai_api.chat.completions.create.return_value = mock_response

        # Create very long content (>3000 chars)
        long_content = "a" * 5000

        tracer._ai_extract_source(
            statistic_text="test",
            article_content=long_content,
            article_url="https://test.com"
        )

        # Check that the content passed to OpenAI was truncated
        call_args = mock_openai_api.chat.completions.create.call_args
        messages = call_args[1]['messages']
        prompt = messages[1]['content']

        # The prompt should contain truncated content with "..."
        assert "..." in prompt
