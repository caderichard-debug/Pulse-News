"""
Tests for Source Tracer Service
"""
import pytest
from unittest.mock import Mock, patch
from sqlmodel import Session
from .services.source_tracer import SourceTracer, get_source_tracer


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

        # Mock AI responses for multi-turn reasoning
        mock_response_1 = Mock()
        mock_response_1.choices = [Mock(message=Mock(content='''
        {
            "source_url": "https://nih.gov/study",
            "source_name": "National Institutes of Health",
            "source_excerpt": "NIH study shows...",
            "confidence": 0.88
        }
        '''))]

        mock_response_2 = Mock()
        mock_response_2.choices = [Mock(message=Mock(content='''
        {
            "verified": true,
            "confidence_adjustment": 0.05,
            "alternative_source": null,
            "reasoning": "Article clearly cites NIH"
        }
        '''))]

        mock_openai_api.chat.completions.create.side_effect = [
            mock_response_1,
            mock_response_2
        ]

        # Article content must contain the source name near the statistic for validation
        result = tracer.trace_statistic_source(
            statistic_text="50% effectiveness",
            article_content="According to the National Institutes of Health study, the treatment shows 50% effectiveness. https://nih.gov/study",
            article_url="https://news.com/article",
            session=None
        )

        assert result is not None
        assert result["source_name"] == "National Institutes of Health"
        assert result["source_url"] == "https://nih.gov/study"

    @patch('app.services.source_tracer.settings')
    @patch('app.services.source_tracer.openai_api')
    def test_trace_statistic_source_ai_fails_uses_nearby_url(self, mock_openai_api, mock_settings):
        """Test that nearby URLs are used when AI finds a source near the statistic"""
        # Disable web search for this test
        mock_settings.google_fact_check_api_key = None

        tracer = SourceTracer()

        # Mock AI responses for multi-turn reasoning
        mock_response_1 = Mock()
        mock_response_1.choices = [Mock(message=Mock(content='''
        {
            "source_url": null,
            "source_name": "Research Organization",
            "source_excerpt": "The study found...",
            "confidence": 0.5
        }
        '''))]

        mock_response_2 = Mock()
        mock_response_2.choices = [Mock(message=Mock(content='''
        {
            "verified": true,
            "confidence_adjustment": 0.0,
            "alternative_source": null,
            "reasoning": "Source mentioned in article"
        }
        '''))]

        mock_openai_api.chat.completions.create.side_effect = [
            mock_response_1,
            mock_response_2
        ]

        # Article with source name near the statistic AND a nearby URL
        article_with_url = "The Research Organization study (https://research.org/data) found 75% success rate."

        result = tracer.trace_statistic_source(
            statistic_text="75%",
            article_content=article_with_url,
            article_url="https://news.com/article",
            session=None
        )

        # Should use nearby URL
        assert result is not None
        assert result["source_url"] == "https://research.org/data"
        assert result["source_name"] == "Research Organization"
        # Confidence should be adjusted
        assert result["confidence"] <= 0.65

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

    def test_extract_references_section_success(self):
        """Test extracting references section from article"""
        tracer = SourceTracer()

        article = """
        This is the main article content about a study.

        Sources:
        - CDC Health Report 2024
        - Johns Hopkins Study on COVID-19

        More content here.
        """

        references = tracer._extract_references_section(article)

        assert references is not None
        assert "CDC" in references
        assert "Johns Hopkins" in references

    def test_extract_references_section_various_patterns(self):
        """Test different reference section patterns"""
        tracer = SourceTracer()

        patterns = [
            "References:\n- Source 1\n- Source 2",
            "Sources:\nCDC Report",
            "This article cites:\nNIH Data",
            "Learn more:\nhttps://example.com",
        ]

        for article in patterns:
            references = tracer._extract_references_section(article)
            assert references is not None

    def test_extract_references_section_not_found(self):
        """Test when no references section exists"""
        tracer = SourceTracer()

        article = "Just a normal article with no references section."

        references = tracer._extract_references_section(article)

        assert references is None

    def test_get_relevant_context_with_statistic(self):
        """Test context extraction when statistic is found"""
        tracer = SourceTracer()

        # Create article with statistic in the middle
        article = "x" * 2000 + "The key statistic is 75%" + "y" * 2000

        context = tracer._get_relevant_context("75%", article, None, max_chars=3000)

        # Should include context around the statistic
        assert "75%" in context
        assert len(context) <= 3100  # Max chars + buffer

    def test_get_relevant_context_with_references(self):
        """Test context includes references section"""
        tracer = SourceTracer()

        article = "Main content here"
        references = "Sources: CDC, NIH"

        context = tracer._get_relevant_context("test", article, references)

        assert "CDC" in context
        assert "REFERENCES SECTION" in context

    def test_get_relevant_context_fallback_strategy(self):
        """Test beginning + end strategy when statistic not found"""
        tracer = SourceTracer()

        # Long article without the statistic - needs to exceed max_chars
        # to trigger the fallback strategy
        article = "Beginning unique content " + "x" * 4000 + " END_MARKER with unique text"

        context = tracer._get_relevant_context("missing stat", article, max_chars=3000)

        # Should include beginning
        assert "Beginning unique content" in context
        # Should include the "article continues" separator (proves fallback was used)
        assert "article continues" in context
        # The very end might be truncated, but we should see the last 1000 chars strategy was attempted
        assert len(context) <= 3100  # Around max_chars

    def test_verify_organization_exists_known_org(self):
        """Test verification for known organizations"""
        tracer = SourceTracer()

        test_cases = [
            ("CDC", "government"),
            ("Pew Research Center", "research"),
            ("Harvard University", "academic"),
            ("World Health Organization", "international"),
            ("Reuters", "media"),
        ]

        for org_name, expected_category in test_cases:
            result = tracer._verify_organization_exists(org_name)

            assert result['verified'] is True
            assert result['category'] == expected_category
            assert result['confidence'] >= 0.9

    def test_verify_organization_exists_heuristic_patterns(self):
        """Test verification using heuristic patterns"""
        tracer = SourceTracer()

        test_cases = [
            ("Random University", "academic"),
            ("Research Institute", "research"),
            ("Federal Bureau", "government"),
            ("Health Agency", "government"),
            ("Science Foundation", "research"),
        ]

        for org_name, expected_category in test_cases:
            result = tracer._verify_organization_exists(org_name)

            assert result['verified'] is True
            assert result['category'] == expected_category
            assert result['confidence'] >= 0.65

    @patch('app.services.source_tracer.settings')
    def test_verify_organization_exists_unknown(self, mock_settings):
        """Test verification for unknown organization"""
        # Mock settings to disable web search fallback
        mock_settings.google_fact_check_api_key = None

        tracer = SourceTracer()

        result = tracer._verify_organization_exists("Random Blog XYZ")

        assert result['verified'] is False
        assert result['category'] == 'unknown'

    @patch('app.services.source_tracer.openai_api')
    def test_ai_extract_source_with_reasoning(self, mock_openai_api):
        """Test multi-turn AI extraction with verification"""
        tracer = SourceTracer()

        # Mock first response (extraction)
        mock_response_1 = Mock()
        mock_response_1.choices = [Mock(message=Mock(content='''
        {
            "source_url": "https://cdc.gov/report",
            "source_name": "CDC",
            "source_excerpt": "According to CDC...",
            "confidence": 0.8
        }
        '''))]

        # Mock second response (verification)
        mock_response_2 = Mock()
        mock_response_2.choices = [Mock(message=Mock(content='''
        {
            "verified": true,
            "confidence_adjustment": 0.1,
            "alternative_source": null,
            "reasoning": "The article clearly mentions CDC as the source"
        }
        '''))]

        mock_openai_api.chat.completions.create.side_effect = [
            mock_response_1,
            mock_response_2
        ]

        result = tracer._ai_extract_source_with_reasoning(
            statistic_text="50% increase",
            article_content="According to CDC, there's a 50% increase",
            article_url="https://test.com"
        )

        assert result is not None
        assert result['source_name'] == "CDC"
        assert result['ai_verified'] is True
        assert result['confidence'] == 0.9  # 0.8 + 0.1 adjustment
        assert 'verification_reasoning' in result

    @patch('app.services.source_tracer.openai_api')
    def test_ai_extract_source_with_reasoning_alternative_source(self, mock_openai_api):
        """Test multi-turn extraction when verification finds alternative source"""
        tracer = SourceTracer()

        # Mock first response
        mock_response_1 = Mock()
        mock_response_1.choices = [Mock(message=Mock(content='''
        {
            "source_url": null,
            "source_name": "Wrong Source",
            "source_excerpt": "...",
            "confidence": 0.5
        }
        '''))]

        # Mock second response with alternative
        mock_response_2 = Mock()
        mock_response_2.choices = [Mock(message=Mock(content='''
        {
            "verified": false,
            "confidence_adjustment": -0.2,
            "alternative_source": "Correct Source",
            "reasoning": "Actually mentions a different organization"
        }
        '''))]

        mock_openai_api.chat.completions.create.side_effect = [
            mock_response_1,
            mock_response_2
        ]

        result = tracer._ai_extract_source_with_reasoning(
            statistic_text="test",
            article_content="content",
            article_url="https://test.com"
        )

        assert result is not None
        assert result['source_name'] == "Correct Source"
        assert result['ai_verified'] is False

    @patch('app.services.source_tracer.openai_api')
    def test_trace_within_article_enhanced(self, mock_openai_api):
        """Test enhanced article tracing with all improvements"""
        tracer = SourceTracer()

        # Mock multi-turn AI responses
        mock_response_1 = Mock()
        mock_response_1.choices = [Mock(message=Mock(content='''
        {
            "source_url": "https://bls.gov/report",
            "source_name": "Bureau of Labor Statistics",
            "source_excerpt": "BLS reports...",
            "confidence": 0.85
        }
        '''))]

        mock_response_2 = Mock()
        mock_response_2.choices = [Mock(message=Mock(content='''
        {
            "verified": true,
            "confidence_adjustment": 0.05,
            "alternative_source": null,
            "reasoning": "Clearly cited in article"
        }
        '''))]

        mock_openai_api.chat.completions.create.side_effect = [
            mock_response_1,
            mock_response_2
        ]

        article = """
        According to the Bureau of Labor Statistics, unemployment fell to 3.5%.

        Sources:
        - BLS Employment Report
        """

        result = tracer._trace_within_article(
            statistic_text="3.5%",
            article_content=article,
            article_url="https://test.com"
        )

        assert result is not None
        assert result['source_name'] == "Bureau of Labor Statistics"
        assert result['organization_verified'] is True
        assert result['organization_category'] == 'government'
        # Confidence boosted by org verification
        assert result['confidence'] >= 0.9
