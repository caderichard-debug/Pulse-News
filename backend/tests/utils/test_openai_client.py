"""
Unit tests for OpenAI client wrapper.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.utils.openai_client import OpenAIClient
import json


class TestOpenAIClientInitialization:
    """Test OpenAI client initialization"""

    @patch('app.utils.openai_client.settings')
    def test_client_initializes_with_api_key(self, mock_settings):
        """Test that client initializes when API key is present"""
        mock_settings.openai_api_key = "sk-test123"
        mock_settings.ai_model = "gpt-4o-mini"

        with patch('app.utils.openai_client.OpenAI') as mock_openai:
            client = OpenAIClient()
            assert client.is_available() is True
            mock_openai.assert_called_once_with(api_key="sk-test123")

    @patch('app.utils.openai_client.settings')
    def test_client_handles_missing_api_key(self, mock_settings):
        """Test that client handles missing API key gracefully"""
        mock_settings.openai_api_key = None

        client = OpenAIClient()
        assert client.is_available() is False
        assert client.client is None


class TestBatchAnalysis:
    """Test batch article analysis"""

    @patch('app.utils.openai_client.settings')
    def test_analyze_articles_batch_success(self, mock_settings):
        """Test successful batch analysis"""
        mock_settings.openai_api_key = "sk-test123"
        mock_settings.ai_model = "gpt-4o-mini"

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "analyses": [
                {
                    "summary": "Test summary",
                    "sentiment_score": 5,
                    "political_lean": "CENTER",
                    "bias_indicators": "neutral",
                    "key_stats": ["stat1", "stat2"]
                }
            ]
        })
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50

        with patch('app.utils.openai_client.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            client = OpenAIClient()
            articles = [{"title": "Test", "content": "Test content"}]
            result = client.analyze_articles_batch(articles)

            assert result is not None
            assert len(result) == 1
            assert result[0]["summary"] == "Test summary"
            assert result[0]["sentiment_score"] == 5

    @patch('app.utils.openai_client.settings')
    def test_analyze_articles_batch_empty_list(self, mock_settings):
        """Test batch analysis with empty article list"""
        mock_settings.openai_api_key = "sk-test123"
        mock_settings.ai_model = "gpt-4o-mini"

        with patch('app.utils.openai_client.OpenAI'):
            client = OpenAIClient()
            result = client.analyze_articles_batch([])
            assert result == []

    @patch('app.utils.openai_client.settings')
    def test_analyze_articles_batch_no_api_key(self, mock_settings):
        """Test batch analysis without API key"""
        mock_settings.openai_api_key = None

        client = OpenAIClient()
        articles = [{"title": "Test", "content": "Test content"}]
        result = client.analyze_articles_batch(articles)

        assert result is None

    @patch('app.utils.openai_client.settings')
    def test_analyze_articles_batch_json_decode_error(self, mock_settings):
        """Test handling of invalid JSON response"""
        mock_settings.openai_api_key = "sk-test123"
        mock_settings.ai_model = "gpt-4o-mini"

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50

        with patch('app.utils.openai_client.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            client = OpenAIClient()
            articles = [{"title": "Test", "content": "Test"}]
            result = client.analyze_articles_batch(articles)

            assert result is None

    @patch('app.utils.openai_client.settings')
    def test_analyze_articles_batch_api_error(self, mock_settings):
        """Test handling of API errors"""
        mock_settings.openai_api_key = "sk-test123"
        mock_settings.ai_model = "gpt-4o-mini"

        with patch('app.utils.openai_client.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_openai.return_value = mock_client

            client = OpenAIClient()
            articles = [{"title": "Test", "content": "Test"}]
            result = client.analyze_articles_batch(articles)

            assert result is None


class TestFrameworkGeneration:
    """Test framework generation"""

    @patch('app.utils.openai_client.settings')
    def test_generate_frameworks_success(self, mock_settings):
        """Test successful framework generation"""
        mock_settings.openai_api_key = "sk-test123"
        mock_settings.ai_model = "gpt-4o-mini"

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "frameworks": [
                {
                    "name": "Privacy vs Security",
                    "description": "Balance between privacy and security",
                    "axis_description": "Level of surveillance",
                    "left_position": "Maximum privacy",
                    "right_position": "Maximum security"
                }
            ]
        })

        with patch('app.utils.openai_client.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            client = OpenAIClient()
            result = client.generate_frameworks(
                article_summaries=["Test summary"],
                existing_frameworks=["Framework 1"]
            )

            assert result is not None
            assert len(result) == 1
            assert result[0]["name"] == "Privacy vs Security"

    @patch('app.utils.openai_client.settings')
    def test_generate_frameworks_no_api_key(self, mock_settings):
        """Test framework generation without API key"""
        mock_settings.openai_api_key = None

        client = OpenAIClient()
        result = client.generate_frameworks(
            article_summaries=["Test"],
            existing_frameworks=[]
        )

        assert result is None


class TestArticleToFrameworkMapping:
    """Test mapping articles to frameworks"""

    @patch('app.utils.openai_client.settings')
    def test_map_article_to_frameworks_success(self, mock_settings):
        """Test successful article to framework mapping"""
        mock_settings.openai_api_key = "sk-test123"
        mock_settings.ai_model = "gpt-4o-mini"

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "mappings": [
                {
                    "framework_id": 1,
                    "relevance_score": 0.8,
                    "position_on_axis": -3,
                    "explanation": "Test explanation"
                }
            ]
        })

        with patch('app.utils.openai_client.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            client = OpenAIClient()
            frameworks = [{
                "id": 1,
                "name": "Test Framework",
                "description": "Test",
                "axis_description": "Test axis",
                "left_position": "Left",
                "right_position": "Right"
            }]

            result = client.map_article_to_frameworks(
                article_title="Test Article",
                article_summary="Test summary",
                frameworks=frameworks
            )

            assert result is not None
            assert len(result) == 1
            assert result[0]["framework_id"] == 1
            assert result[0]["relevance_score"] == 0.8

    @patch('app.utils.openai_client.settings')
    def test_map_article_to_frameworks_no_api_key(self, mock_settings):
        """Test mapping without API key"""
        mock_settings.openai_api_key = None

        client = OpenAIClient()
        result = client.map_article_to_frameworks(
            article_title="Test",
            article_summary="Test",
            frameworks=[]
        )

        assert result is None


class TestCostCalculation:
    """Test cost calculation"""

    @patch('app.utils.openai_client.settings')
    def test_calculate_cost_accuracy(self, mock_settings):
        """Test that cost calculation is accurate"""
        mock_settings.openai_api_key = "sk-test123"

        with patch('app.utils.openai_client.OpenAI'):
            client = OpenAIClient()

            # Test with known values
            # Input: 1000 tokens @ $0.15/1M = $0.00015
            # Output: 500 tokens @ $0.60/1M = $0.00030
            # Total: $0.00045
            cost = client._calculate_cost(1000, 500)
            assert abs(cost - 0.00045) < 0.000001

            # Test with larger values
            cost = client._calculate_cost(100000, 50000)
            assert abs(cost - 0.045) < 0.000001

    @patch('app.utils.openai_client.settings')
    def test_calculate_cost_zero_tokens(self, mock_settings):
        """Test cost calculation with zero tokens"""
        mock_settings.openai_api_key = "sk-test123"

        with patch('app.utils.openai_client.OpenAI'):
            client = OpenAIClient()
            cost = client._calculate_cost(0, 0)
            assert cost == 0.0

    @patch('app.utils.openai_client.snapshot')
    @patch('app.utils.openai_client.settings')
    def test_resolve_model_uses_fallback_when_budget_threshold_exceeded(
        self,
        mock_settings,
        mock_snapshot,
    ):
        """Model should switch to fallback when spend reaches warning threshold."""
        mock_settings.openai_api_key = "sk-test123"
        mock_settings.ai_model = "gpt-4o"
        mock_settings.fallback_ai_model = "gpt-4o-mini"
        mock_settings.pipeline_daily_budget_usd = 10.0
        mock_settings.pipeline_warn_budget_percent = 0.8
        mock_snapshot.return_value = {"costs_usd": {"pipeline_total": 8.01}}

        with patch('app.utils.openai_client.OpenAI'):
            client = OpenAIClient()
            assert client._resolve_model() == "gpt-4o-mini"


class TestPromptBuilding:
    """Test prompt building functions"""

    @patch('app.utils.openai_client.settings')
    def test_build_batch_analysis_prompt(self, mock_settings):
        """Test batch analysis prompt building"""
        mock_settings.openai_api_key = "sk-test123"

        with patch('app.utils.openai_client.OpenAI'):
            client = OpenAIClient()
            articles = [
                {"title": "Article 1", "content": "Content 1"},
                {"title": "Article 2", "content": "Content 2"}
            ]

            prompt = client._build_batch_analysis_prompt(articles)

            assert "Article 1" in prompt
            assert "Article 2" in prompt
            assert "Content 1" in prompt
            assert "Content 2" in prompt
            assert "Summary" in prompt
            assert "Sentiment" in prompt
            assert "Political Lean" in prompt

    @patch('app.utils.openai_client.settings')
    def test_build_framework_mapping_prompt(self, mock_settings):
        """Test framework mapping prompt building"""
        mock_settings.openai_api_key = "sk-test123"

        with patch('app.utils.openai_client.OpenAI'):
            client = OpenAIClient()
            frameworks = [{
                "id": 1,
                "name": "Test Framework",
                "description": "Test description",
                "axis_description": "Test axis",
                "left_position": "Left",
                "right_position": "Right"
            }]

            prompt = client._build_framework_mapping_prompt(
                article_title="Test Article",
                article_summary="Test summary",
                frameworks=frameworks
            )

            assert "Test Article" in prompt
            assert "Test summary" in prompt
            assert "Test Framework" in prompt
            assert "Test description" in prompt
            assert "relevance score" in prompt

    @patch('app.utils.openai_client.settings')
    def test_build_framework_discovery_prompt(self, mock_settings):
        """Test framework discovery prompt building"""
        mock_settings.openai_api_key = "sk-test123"

        with patch('app.utils.openai_client.OpenAI'):
            client = OpenAIClient()
            summaries = ["Summary 1", "Summary 2"]
            existing = ["Framework 1", "Framework 2"]

            prompt = client._build_framework_discovery_prompt(summaries, existing)

            assert "Summary 1" in prompt
            assert "Summary 2" in prompt
            assert "Framework 1" in prompt
            assert "Framework 2" in prompt
            assert "NEW ethical or moral debates" in prompt
