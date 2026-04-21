"""
Fact Check Integrator Service

Integrates with external fact-checking APIs to verify statistics.
Supports:
- Google Fact Check Tools API
- ClaimBuster API
- Optional PolitiFact / Snopes HTML search (see FACT_CHECK_ENABLE_SCRAPING)
"""

import logging
import requests
from typing import Optional, Dict, List
from urllib.parse import quote
from datetime import datetime

from ..config import settings
from .fact_check_scrape.politifact import search_politifact_claim
from .fact_check_scrape.snopes import search_snopes_claim
from .fact_check_scrape.rating_parser import parse_textual_rating_to_status

logger = logging.getLogger(__name__)

# Prefer structured API results unless confidence is below this (then try HTML scrapers).
_SCRAPE_FALLBACK_MAX_CONFIDENCE = 0.55


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
        results: List[Dict] = []

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

        def _best(rs: List[Dict]) -> Optional[Dict]:
            if not rs:
                return None
            return max(rs, key=lambda r: r.get("confidence", 0.0))

        best_result = _best(results)

        # Lightweight HTML search when APIs miss or yield low-confidence only
        if getattr(settings, "fact_check_enable_scraping", True):
            ua = settings.fact_check_scrape_user_agent or (
                "PulseNews/1.0 (+https://pulsenews.app; fact-check verification)"
            )
            need_scrape = best_result is None or best_result.get("confidence", 0.0) < _SCRAPE_FALLBACK_MAX_CONFIDENCE
            if need_scrape:
                pf = self._check_politifact_web_scraping(statistic_text, user_agent=ua)
                if pf:
                    results.append(pf)
                    best_result = _best(results)
                if best_result is None or best_result.get("confidence", 0.0) < _SCRAPE_FALLBACK_MAX_CONFIDENCE:
                    sn = self._check_snopes_web_scraping(statistic_text, user_agent=ua)
                    if sn:
                        results.append(sn)
                        best_result = _best(results)

        if not best_result:
            logger.debug(f"No fact-check found for: {statistic_text[:50]}")
            return None

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
            status = parse_textual_rating_to_status(rating_text)

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

    def _check_politifact_web_scraping(self, claim: str, user_agent: str) -> Optional[Dict]:
        """
        Search PolitiFact (HTML search). Layouts can change; failures are non-fatal.
        """
        try:
            return search_politifact_claim(claim, user_agent=user_agent)
        except Exception as e:
            logger.debug("PolitiFact scrape error: %s", e)
            return None

    def _check_snopes_web_scraping(self, claim: str, user_agent: str) -> Optional[Dict]:
        """Search Snopes (HTML search). Layouts can change; failures are non-fatal."""
        try:
            return search_snopes_claim(claim, user_agent=user_agent)
        except Exception as e:
            logger.debug("Snopes scrape error: %s", e)
            return None


# Singleton instance
_fact_check_integrator = None


def get_fact_check_integrator() -> FactCheckIntegrator:
    """Get singleton instance of FactCheckIntegrator."""
    global _fact_check_integrator
    if _fact_check_integrator is None:
        _fact_check_integrator = FactCheckIntegrator()
    return _fact_check_integrator
