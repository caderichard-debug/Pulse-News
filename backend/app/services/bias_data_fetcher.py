"""
Bias Data Fetcher Service

Fetches organizational bias ratings for news sources from external APIs.
Primary source: AllSides Media Bias Ratings
Fallback: Manual lookup table for common sources
"""

import logging
from typing import Optional, Dict, Tuple
from urllib.parse import urlparse
import httpx

from app.models import OrganizationalBias

logger = logging.getLogger(__name__)


# Fallback bias lookup table for common news sources
MANUAL_BIAS_LOOKUP = {
    # Wire Services / Fact-Based
    "apnews.com": {
        "bias": OrganizationalBias.CENTER,
        "description": "Wire service known for factual, neutral reporting with minimal editorial content.",
        "confidence": 0.95
    },
    "reuters.com": {
        "bias": OrganizationalBias.CENTER,
        "description": "International wire service with reputation for objective, fact-based journalism.",
        "confidence": 0.95
    },
    "bloomberg.com": {
        "bias": OrganizationalBias.CENTER,
        "description": "Financial news service with focus on business and economics reporting.",
        "confidence": 0.90
    },

    # Center-Left
    "npr.org": {
        "bias": OrganizationalBias.CENTER_LEFT,
        "description": "US public radio network with progressive cultural coverage and in-depth reporting.",
        "confidence": 0.90
    },
    "bbc.com": {
        "bias": OrganizationalBias.CENTER_LEFT,
        "description": "British public broadcaster with slight progressive lean, known for comprehensive international coverage.",
        "confidence": 0.85
    },
    "nytimes.com": {
        "bias": OrganizationalBias.CENTER_LEFT,
        "description": "Mainstream liberal editorial stance with comprehensive national and international coverage.",
        "confidence": 0.90
    },
    "washingtonpost.com": {
        "bias": OrganizationalBias.CENTER_LEFT,
        "description": "Progressive editorial stance with investigative journalism focus.",
        "confidence": 0.90
    },
    "theatlantic.com": {
        "bias": OrganizationalBias.CENTER_LEFT,
        "description": "Long-form journalism with intellectual, progressive editorial perspective.",
        "confidence": 0.85
    },
    "theguardian.com": {
        "bias": OrganizationalBias.CENTER_LEFT,
        "description": "British newspaper with left-leaning editorial stance and global coverage.",
        "confidence": 0.90
    },
    "cnn.com": {
        "bias": OrganizationalBias.CENTER_LEFT,
        "description": "Cable news network with center-left editorial perspective.",
        "confidence": 0.85
    },
    "msnbc.com": {
        "bias": OrganizationalBias.LEFT,
        "description": "Cable news network with progressive/liberal editorial stance.",
        "confidence": 0.90
    },
    "huffpost.com": {
        "bias": OrganizationalBias.LEFT,
        "description": "Progressive news and opinion website with liberal editorial focus.",
        "confidence": 0.95
    },

    # Center
    "politico.com": {
        "bias": OrganizationalBias.CENTER,
        "description": "Political journalism outlet covering perspectives from across the spectrum.",
        "confidence": 0.85
    },
    "csmonitor.com": {
        "bias": OrganizationalBias.CENTER,
        "description": "International news organization known for balanced, thoughtful reporting.",
        "confidence": 0.90
    },
    "usatoday.com": {
        "bias": OrganizationalBias.CENTER,
        "description": "National newspaper with centrist news coverage.",
        "confidence": 0.85
    },
    "axios.com": {
        "bias": OrganizationalBias.CENTER,
        "description": "Digital news service with concise, non-partisan reporting style.",
        "confidence": 0.85
    },

    # Center-Right
    "wsj.com": {
        "bias": OrganizationalBias.CENTER_RIGHT,
        "description": "Business-focused newspaper with conservative editorial page, centrist news reporting.",
        "confidence": 0.90
    },
    "economist.com": {
        "bias": OrganizationalBias.CENTER_RIGHT,
        "description": "British magazine with classical liberal (center-right) economic perspective.",
        "confidence": 0.85
    },
    "thehill.com": {
        "bias": OrganizationalBias.CENTER_RIGHT,
        "description": "Political news outlet with slight conservative lean.",
        "confidence": 0.80
    },

    # Right
    "foxnews.com": {
        "bias": OrganizationalBias.RIGHT,
        "description": "Cable news network with conservative editorial perspective.",
        "confidence": 0.95
    },
    "nationalreview.com": {
        "bias": OrganizationalBias.RIGHT,
        "description": "Conservative magazine and website with right-leaning editorial stance.",
        "confidence": 0.95
    },
    "wsj.com": {
        "bias": OrganizationalBias.CENTER_RIGHT,
        "description": "Business newspaper with conservative editorial page.",
        "confidence": 0.90
    },
    "nypost.com": {
        "bias": OrganizationalBias.RIGHT,
        "description": "Tabloid newspaper with conservative editorial perspective.",
        "confidence": 0.90
    },

    # Tech/Specialized (Generally Center)
    "arstechnica.com": {
        "bias": OrganizationalBias.CENTER,
        "description": "Technology-focused publication with minimal political bias in reporting.",
        "confidence": 0.90
    },
    "theverge.com": {
        "bias": OrganizationalBias.CENTER,
        "description": "Technology and culture website with generally neutral reporting.",
        "confidence": 0.85
    },
    "wired.com": {
        "bias": OrganizationalBias.CENTER_LEFT,
        "description": "Technology magazine with slight progressive lean in cultural coverage.",
        "confidence": 0.80
    },
}


def extract_domain(url: str) -> str:
    """Extract base domain from URL."""
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    # Remove www. prefix
    if domain.startswith("www."):
        domain = domain[4:]
    return domain.lower()


async def fetch_from_allsides(domain: str) -> Optional[Dict]:
    """
    Attempt to fetch bias rating from AllSides Media Bias API.

    Note: AllSides does not have a public API as of 2025.
    This function is a placeholder for future integration if they release one.

    For now, returns None to fall back to manual lookup.
    """
    # TODO: Implement AllSides API integration when/if available
    # AllSides provides bias ratings but requires web scraping or manual lookup
    # Their ratings: Left, Lean Left, Center, Lean Right, Right

    logger.info(f"AllSides API not yet implemented, falling back to manual lookup for {domain}")
    return None


async def fetch_from_media_bias_fact_check(domain: str) -> Optional[Dict]:
    """
    Attempt to fetch bias rating from Media Bias/Fact Check.

    Note: MBFC does not have a public API.
    This is a placeholder for potential web scraping integration.

    For now, returns None to fall back to manual lookup.
    """
    # TODO: Implement MBFC web scraping if needed
    # MBFC provides detailed bias ratings and factual reporting scores
    # Their ratings: Extreme Left, Left, Left-Center, Least Biased, Right-Center, Right, Extreme Right

    logger.info(f"MBFC scraping not yet implemented, falling back to manual lookup for {domain}")
    return None


def map_bias_string_to_enum(bias_string: str) -> Optional[OrganizationalBias]:
    """Map various bias string formats to OrganizationalBias enum."""
    bias_lower = bias_string.lower().strip()

    # Handle AllSides format
    if bias_lower in ["left", "extreme left"]:
        return OrganizationalBias.LEFT
    elif bias_lower in ["lean left", "left-center", "center-left"]:
        return OrganizationalBias.CENTER_LEFT
    elif bias_lower in ["center", "least biased", "mixed"]:
        return OrganizationalBias.CENTER
    elif bias_lower in ["lean right", "right-center", "center-right"]:
        return OrganizationalBias.CENTER_RIGHT
    elif bias_lower in ["right", "extreme right"]:
        return OrganizationalBias.RIGHT

    return None


async def fetch_source_bias(url: str) -> Dict:
    """
    Fetch organizational bias information for a news source.

    Args:
        url: The source's website URL

    Returns:
        Dict with keys:
            - bias: OrganizationalBias enum value (or None)
            - description: str description of the bias
            - confidence: float between 0-1
            - method: str ("api", "manual", "unknown")
    """
    domain = extract_domain(url)

    # Try AllSides API first (placeholder for now)
    allsides_result = await fetch_from_allsides(domain)
    if allsides_result:
        return {
            "bias": map_bias_string_to_enum(allsides_result["bias"]),
            "description": allsides_result.get("description", ""),
            "confidence": allsides_result.get("confidence", 0.85),
            "method": "allsides_api"
        }

    # Try MBFC scraping (placeholder for now)
    mbfc_result = await fetch_from_media_bias_fact_check(domain)
    if mbfc_result:
        return {
            "bias": map_bias_string_to_enum(mbfc_result["bias"]),
            "description": mbfc_result.get("description", ""),
            "confidence": mbfc_result.get("confidence", 0.80),
            "method": "mbfc_scraping"
        }

    # Fall back to manual lookup table
    if domain in MANUAL_BIAS_LOOKUP:
        lookup_data = MANUAL_BIAS_LOOKUP[domain]
        return {
            "bias": lookup_data["bias"],
            "description": lookup_data["description"],
            "confidence": lookup_data["confidence"],
            "method": "manual_lookup"
        }

    # No bias data available
    logger.warning(f"No bias data found for domain: {domain}")
    return {
        "bias": None,
        "description": f"Bias rating not yet available for {domain}. Research needed.",
        "confidence": 0.0,
        "method": "unknown"
    }


async def get_bias_for_source(url: str) -> Tuple[Optional[OrganizationalBias], Optional[str]]:
    """
    Simplified interface to get bias and description for a source.

    Returns:
        Tuple of (bias_enum, description_string)
    """
    result = await fetch_source_bias(url)
    return result["bias"], result["description"]
