"""
Tests for Fact Check Integrator Service
"""
import pytest
from unittest.mock import Mock, patch
from app.services.fact_check_integrator import FactCheckIntegrator, get_fact_check_integrator


class TestFactCheckIntegrator:
    """Test fact-checking API integration"""

    @patch('app.services.fact_check_integrator.requests.get')
    def test_google_fact_check_verified(self, mock_get):
        """Test Google Fact Check API returns verified result"""
        integrator = FactCheckIntegrator()
        integrator.google_api_key = "test_key"

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "claims": [
                {
                    "claimReview": [
                        {
                            "publisher": {"name": "PolitiFact"},
                            "title": "Test Claim",
                            "textualRating": "True",
                            "url": "https://politifact.com/factcheck"
                        }
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response

        result = integrator._check_google_fact_check("Test claim")

        assert result is not None
        assert result["fact_check_status"] == "verified"
        assert result["fact_check_source"] == "google_fact_check"
        assert "PolitiFact" in result["fact_check_details"]

    @patch('app.services.fact_check_integrator.requests.get')
    def test_google_fact_check_false(self, mock_get):
        """Test Google Fact Check API returns false result"""
        integrator = FactCheckIntegrator()
        integrator.google_api_key = "test_key"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "claims": [
                {
                    "claimReview": [
                        {
                            "publisher": {"name": "Snopes"},
                            "title": "False Claim",
                            "textualRating": "False",
                            "url": "https://snopes.com/factcheck"
                        }
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response

        result = integrator._check_google_fact_check("False claim")

        assert result is not None
        assert result["fact_check_status"] == "false"

    @patch('app.services.fact_check_integrator.requests.get')
    def test_google_fact_check_mixed(self, mock_get):
        """Test Google Fact Check API returns mixed result"""
        integrator = FactCheckIntegrator()
        integrator.google_api_key = "test_key"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "claims": [
                {
                    "claimReview": [
                        {
                            "publisher": {"name": "FactCheck.org"},
                            "title": "Mixed Claim",
                            "textualRating": "Mixture",
                            "url": "https://factcheck.org/check"
                        }
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response

        result = integrator._check_google_fact_check("Mixed claim")

        assert result is not None
        assert result["fact_check_status"] == "mixed"

    @patch('app.services.fact_check_integrator.requests.get')
    def test_google_fact_check_no_results(self, mock_get):
        """Test Google Fact Check API with no results"""
        integrator = FactCheckIntegrator()
        integrator.google_api_key = "test_key"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # No claims
        mock_get.return_value = mock_response

        result = integrator._check_google_fact_check("Unknown claim")

        assert result is None

    @patch('app.services.fact_check_integrator.requests.get')
    def test_google_fact_check_api_error(self, mock_get):
        """Test Google Fact Check API error handling"""
        integrator = FactCheckIntegrator()
        integrator.google_api_key = "test_key"

        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = integrator._check_google_fact_check("Test claim")

        assert result is None

    @patch('app.services.fact_check_integrator.requests.get')
    def test_google_fact_check_permission_denied(self, mock_get):
        """Test Google Fact Check API permission denied"""
        integrator = FactCheckIntegrator()
        integrator.google_api_key = "invalid_key"

        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        result = integrator._check_google_fact_check("Test claim")

        assert result is None

    @patch('app.services.fact_check_integrator.requests.post')
    def test_claimbuster_high_score(self, mock_post):
        """Test ClaimBuster API with high fact-checkability score"""
        integrator = FactCheckIntegrator()
        integrator.claimbuster_api_key = "test_key"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"score": 0.85}]
        }
        mock_post.return_value = mock_response

        result = integrator._check_claimbuster("Test claim")

        assert result is not None
        assert result["fact_check_source"] == "claimbuster"
        assert "0.85" in result["fact_check_details"]

    @patch('app.services.fact_check_integrator.requests.post')
    def test_claimbuster_low_score(self, mock_post):
        """Test ClaimBuster API with low score (not worth checking)"""
        integrator = FactCheckIntegrator()
        integrator.claimbuster_api_key = "test_key"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"score": 0.3}]
        }
        mock_post.return_value = mock_response

        result = integrator._check_claimbuster("Not a factual claim")

        # Should return None for low scores
        assert result is None

    @patch('app.services.fact_check_integrator.requests.post')
    def test_claimbuster_unauthorized(self, mock_post):
        """Test ClaimBuster API unauthorized"""
        integrator = FactCheckIntegrator()
        integrator.claimbuster_api_key = "invalid_key"

        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        result = integrator._check_claimbuster("Test claim")

        assert result is None

    def test_parse_google_rating_true(self):
        """Test parsing various 'true' ratings"""
        integrator = FactCheckIntegrator()

        assert integrator._parse_google_rating("True") == "verified"
        assert integrator._parse_google_rating("Correct") == "verified"
        assert integrator._parse_google_rating("Accurate") == "verified"

    def test_parse_google_rating_mostly_true(self):
        """Test parsing 'mostly true' as mixed"""
        integrator = FactCheckIntegrator()

        assert integrator._parse_google_rating("Mostly True") == "mixed"
        assert integrator._parse_google_rating("Partially True") == "mixed"

    def test_parse_google_rating_false(self):
        """Test parsing various 'false' ratings"""
        integrator = FactCheckIntegrator()

        assert integrator._parse_google_rating("False") == "false"
        assert integrator._parse_google_rating("Incorrect") == "false"
        assert integrator._parse_google_rating("Pants on Fire") == "false"

    def test_parse_google_rating_mostly_false(self):
        """Test parsing 'mostly false' as mixed"""
        integrator = FactCheckIntegrator()

        assert integrator._parse_google_rating("Mostly False") == "mixed"

    def test_parse_google_rating_mixed(self):
        """Test parsing mixed ratings"""
        integrator = FactCheckIntegrator()

        assert integrator._parse_google_rating("Mixture") == "mixed"
        assert integrator._parse_google_rating("Half True") == "mixed"
        assert integrator._parse_google_rating("Mixed") == "mixed"

    def test_parse_google_rating_unproven(self):
        """Test parsing unproven ratings"""
        integrator = FactCheckIntegrator()

        assert integrator._parse_google_rating("Unproven") == "unverifiable"
        assert integrator._parse_google_rating("Unclear") == "unverifiable"
        assert integrator._parse_google_rating("Unsupported") == "unverifiable"

    def test_parse_google_rating_unknown(self):
        """Test parsing unknown rating defaults to unverifiable"""
        integrator = FactCheckIntegrator()

        assert integrator._parse_google_rating("Unknown Rating") == "unverifiable"

    @patch('app.services.fact_check_integrator.requests.get')
    def test_verify_statistic_uses_google_first(self, mock_get):
        """Test that verify_statistic tries Google first and uses its result"""
        integrator = FactCheckIntegrator()
        integrator.google_api_key = "test_key"
        integrator.claimbuster_api_key = None  # Disable ClaimBuster for this test

        # Mock Google response
        mock_google_response = Mock()
        mock_google_response.status_code = 200
        mock_google_response.json.return_value = {
            "claims": [{
                "claimReview": [{
                    "publisher": {"name": "Test"},
                    "title": "Test",
                    "textualRating": "True",
                    "url": "https://test.com"
                }]
            }]
        }
        mock_get.return_value = mock_google_response

        result = integrator.verify_statistic("Test claim")

        # Should use Google result
        assert result is not None
        assert result["fact_check_source"] == "google_fact_check"

    @patch('app.services.fact_check_integrator.requests.get')
    @patch('app.services.fact_check_integrator.requests.post')
    def test_verify_statistic_falls_back_to_claimbuster(self, mock_post, mock_get):
        """Test fallback to ClaimBuster when Google returns nothing"""
        integrator = FactCheckIntegrator()
        integrator.google_api_key = "test_key"
        integrator.claimbuster_api_key = "test_key"

        # Mock Google with no results
        mock_google_response = Mock()
        mock_google_response.status_code = 200
        mock_google_response.json.return_value = {}
        mock_get.return_value = mock_google_response

        # Mock ClaimBuster with result
        mock_cb_response = Mock()
        mock_cb_response.status_code = 200
        mock_cb_response.json.return_value = {
            "results": [{"score": 0.8}]
        }
        mock_post.return_value = mock_cb_response

        result = integrator.verify_statistic("Test claim")

        # Should use ClaimBuster result
        assert result is not None
        assert result["fact_check_source"] == "claimbuster"

    def test_verify_statistic_no_api_keys(self):
        """Test verify_statistic with no API keys configured"""
        integrator = FactCheckIntegrator()
        integrator.google_api_key = None
        integrator.claimbuster_api_key = None

        result = integrator.verify_statistic("Test claim")

        assert result is None

    @patch('app.services.fact_check_integrator.requests.get')
    def test_verify_statistic_selects_highest_confidence(self, mock_get):
        """Test that verify_statistic selects result with highest confidence"""
        integrator = FactCheckIntegrator()
        integrator.google_api_key = "test_key"

        # Mock response with trusted publisher (higher confidence)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "claims": [{
                "claimReview": [{
                    "publisher": {"name": "Snopes"},  # Trusted publisher
                    "title": "Test",
                    "textualRating": "True",
                    "url": "https://snopes.com"
                }]
            }]
        }
        mock_get.return_value = mock_response

        result = integrator._check_google_fact_check("Test")

        # Snopes should boost confidence to 0.85
        assert result["confidence"] == 0.85

    def test_get_fact_check_integrator_singleton(self):
        """Test singleton pattern"""
        integrator1 = get_fact_check_integrator()
        integrator2 = get_fact_check_integrator()

        assert integrator1 is integrator2

    @patch('app.services.fact_check_integrator.requests.get')
    def test_google_fact_check_request_exception(self, mock_get):
        """Test handling of request exceptions"""
        integrator = FactCheckIntegrator()
        integrator.google_api_key = "test_key"

        # Mock request exception
        mock_get.side_effect = Exception("Network error")

        result = integrator._check_google_fact_check("Test")

        assert result is None

    @patch('app.services.fact_check_integrator.requests.post')
    def test_claimbuster_request_exception(self, mock_post):
        """Test handling of ClaimBuster request exceptions"""
        integrator = FactCheckIntegrator()
        integrator.claimbuster_api_key = "test_key"

        # Mock request exception
        mock_post.side_effect = Exception("Network error")

        result = integrator._check_claimbuster("Test")

        assert result is None
