"""
Fact Check Integrator Service

Integrates with external fact-checking APIs to verify statistics.
Supports:
- Google Fact Check Tools API
- ClaimBuster API
- Future: PolitiFact, Snopes (web scraping)
"""

import logging
import requests
from typing import Optional, Dict, List
from urllib.parse import quote
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


class FactCheckIntegrator:
    """Service for integrating with fact-checking APIs."""

    def __init__(self):
        self.google_api_key = settings.google_fact_check_api_key
        self.claimbuster_api_key = settings.claimbuster_api_key

    def verify_statistic(
        self,
        statistic_text: str,
        source_url: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Check statistic against external fact-checking services.

        Args:
            statistic_text: The statistic to verify
            source_url: Optional URL of the original source

        Returns:
            Dict with keys:
                - fact_check_status: "verified" | "false" | "mixed" | "unverifiable"
                - fact_check_source: "google_fact_check" | "claimbuster" | etc.
                - fact_check_url: URL to the fact-check result
                - fact_check_details: Full explanation
                - confidence: 0.0 to 1.0
            Returns None if no fact-check found
        """
        results = []

        # Try Google Fact Check Tools first (best coverage)
        if self.google_api_key:
            google_result = self._check_google_fact_check(statistic_text)
            if google_result:
                results.append(google_result)

        # Try ClaimBuster (fact-checkability score)
        if self.claimbuster_api_key:
            claimbuster_result = self._check_claimbuster(statistic_text)
            if claimbuster_result:
                results.append(claimbuster_result)

        # Select best result
        if not results:
            logger.debug(f"No fact-check found for: {statistic_text[:50]}")
            return None

        # Prefer results with higher confidence
        best_result = max(results, key=lambda r: r.get("confidence", 0.0))

        logger.info(
            f"Fact-check found via {best_result['fact_check_source']}: "
            f"{best_result['fact_check_status']} (confidence: {best_result.get('confidence', 0.0):.2f})"
        )

        return best_result

    def _check_google_fact_check(self, claim: str) -> Optional[Dict]:
        """
        Query Google Fact Check Tools API.

        API Docs: https://developers.google.com/fact-check/tools/api/reference/rest/v1alpha1/claims/search
        """
        try:
            url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
            params = {
                "query": claim,
                "key": self.google_api_key,
                "languageCode": "en"
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 403:
                logger.warning("Google Fact Check API: Permission denied - check API key")
                return None

            if response.status_code != 200:
                logger.warning(f"Google Fact Check API returned status {response.status_code}")
                return None

            data = response.json()

            if not data.get("claims"):
                logger.debug("No claims found in Google Fact Check")
                return None

            # Get the first (most relevant) claim
            claim_data = data["claims"][0]
            claim_review = claim_data.get("claimReview", [{}])[0]

            # Extract rating
            rating_text = claim_review.get("textualRating", "").lower()
            status = self._parse_google_rating(rating_text)

            # Calculate confidence based on publisher and rating clarity
            confidence = 0.7
            publisher = claim_review.get("publisher", {}).get("name", "")
            if any(trusted in publisher.lower() for trusted in ["politifact", "snopes", "factcheck.org"]):
                confidence = 0.85

            return {
                "fact_check_status": status,
                "fact_check_source": "google_fact_check",
                "fact_check_url": claim_review.get("url", ""),
                "fact_check_details": f"{publisher}: {claim_review.get('title', '')} - {rating_text}",
                "confidence": confidence
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Google Fact Check API: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing Google Fact Check response: {e}")
            return None

    def _parse_google_rating(self, rating_text: str) -> str:
        """
        Parse Google Fact Check rating into our standard statuses.

        Common ratings: "True", "False", "Mostly True", "Mostly False",
        "Half True", "Mixture", "Unproven", etc.
        """
        rating_lower = rating_text.lower()

        if any(word in rating_lower for word in ["true", "correct", "accurate"]):
            if any(word in rating_lower for word in ["mostly", "partially"]):
                return "mixed"
            else:
                return "verified"

        if any(word in rating_lower for word in ["false", "incorrect", "inaccurate", "pants on fire"]):
            if any(word in rating_lower for word in ["mostly"]):
                return "mixed"
            else:
                return "false"

        if any(word in rating_lower for word in ["mixture", "mixed", "half"]):
            return "mixed"

        if any(word in rating_lower for word in ["unproven", "unclear", "unsupported"]):
            return "unverifiable"

        # Default to unverifiable if we can't parse the rating
        return "unverifiable"

    def _check_claimbuster(self, claim: str) -> Optional[Dict]:
        """
        Query ClaimBuster API for fact-checkability score.

        ClaimBuster checks if a statement is worth fact-checking (0-1 score).
        High scores suggest the claim is factual and checkable.

        API Docs: https://idir.uta.edu/claimbuster/api/
        """
        try:
            # ClaimBuster API endpoint (free tier)
            url = "https://idir.uta.edu/claimbuster/api/v2/score/text"

            headers = {
                "x-api-key": self.claimbuster_api_key
            }

            data = {
                "input_text": claim
            }

            response = requests.post(url, json=data, headers=headers, timeout=10)

            if response.status_code == 401:
                logger.warning("ClaimBuster API: Unauthorized - check API key")
                return None

            if response.status_code != 200:
                logger.warning(f"ClaimBuster API returned status {response.status_code}")
                return None

            result = response.json()

            # ClaimBuster returns a score 0-1 indicating fact-checkability
            # Higher score = more likely to be a factual claim worth checking
            score = result.get("results", [{}])[0].get("score", 0.0)

            if score < 0.5:
                # Low score = not a check-worthy factual claim
                logger.debug(f"ClaimBuster score too low: {score:.2f}")
                return None

            # For ClaimBuster, we can only say if it's worth checking, not the truth value
            # So we return "unverifiable" but with the checkability score
            return {
                "fact_check_status": "unverifiable",
                "fact_check_source": "claimbuster",
                "fact_check_url": "",
                "fact_check_details": f"This claim has a fact-checkability score of {score:.2f} (0-1 scale). Higher scores indicate the claim is factual and worth fact-checking.",
                "confidence": score * 0.6  # Convert to our confidence scale
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling ClaimBuster API: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing ClaimBuster response: {e}")
            return None

    def _check_politifact_web_scraping(self, claim: str) -> Optional[Dict]:
        """
        Search PolitiFact via web scraping (no official API).

        Note: This is a placeholder for future implementation.
        Would require Beautiful Soup and careful parsing of search results.
        """
        # TODO: Implement web scraping for PolitiFact
        logger.debug("PolitiFact web scraping not yet implemented")
        return None

    def _check_snopes_web_scraping(self, claim: str) -> Optional[Dict]:
        """
        Search Snopes via web scraping (no official API).

        Note: This is a placeholder for future implementation.
        Would require Beautiful Soup and careful parsing of search results.
        """
        # TODO: Implement web scraping for Snopes
        logger.debug("Snopes web scraping not yet implemented")
        return None


# Singleton instance
_fact_check_integrator = None


def get_fact_check_integrator() -> FactCheckIntegrator:
    """Get singleton instance of FactCheckIntegrator."""
    global _fact_check_integrator
    if _fact_check_integrator is None:
        _fact_check_integrator = FactCheckIntegrator()
    return _fact_check_integrator
