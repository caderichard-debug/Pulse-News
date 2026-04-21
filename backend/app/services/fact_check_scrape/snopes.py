"""
Lightweight Snopes search scrape (no official API).
Defensive parsing; layouts change.
"""

from __future__ import annotations

import logging
import re
from typing import Callable, Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from .rating_parser import parse_textual_rating_to_status

logger = logging.getLogger(__name__)

SNOPES_SEARCH = "https://www.snopes.com/"
MAX_RESPONSE_BYTES = 600_000
DEFAULT_TIMEOUT = 8
MAX_CANDIDATES = 3


def _default_headers(user_agent: str) -> dict:
    return {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }


def _truncate(s: str, max_len: int = 400) -> str:
    s = (s or "").strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."


def _normalize_snopes_href(href: str, base: str = "https://www.snopes.com") -> Optional[str]:
    href = href.strip()
    if not href:
        return None
    if "/fact-check/" not in href.lower() and "/fact_check/" not in href.lower():
        return None
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return base.rstrip("/") + href
    if href.startswith("http"):
        return href
    return None


def parse_snopes_search_html(html: str) -> Optional[dict]:
    """Parse Snopes search / listing HTML for first fact-check links."""
    if not html or len(html) < 200:
        return None

    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception as e:  # pragma: no cover
        logger.debug("Snopes parse soup error: %s", e)
        return None

    candidates = []
    for a in soup.find_all("a", href=True):
        full = _normalize_snopes_href(a["href"])
        if not full:
            continue
        text = _truncate(a.get_text(" ", strip=True) or "")
        if len(text) < 6:
            continue
        if full in {c[0] for c in candidates}:
            continue
        candidates.append((full, text, a))
        if len(candidates) >= MAX_CANDIDATES:
            break

    if not candidates:
        return None

    url, title, first_a = candidates[0]
    rating_guess = ""
    parent = first_a.parent if first_a else None
    if parent:
        block = parent.get_text(" ", strip=True)
        for token in (
            "True",
            "False",
            "Mostly True",
            "Mostly False",
            "Mixture",
            "Unproven",
            "Miscaptioned",
            "Correct Attribution",
        ):
            if token.lower() in block.lower():
                rating_guess = token
                break

    status = parse_textual_rating_to_status(rating_guess) if rating_guess else "unverifiable"
    confidence = 0.7 if rating_guess else 0.5

    return {
        "fact_check_status": status,
        "fact_check_source": "snopes_scrape",
        "fact_check_url": url,
        "fact_check_details": _truncate(
            f"Snopes: {title}" + (f" — {rating_guess}" if rating_guess else "")
        ),
        "confidence": confidence,
    }


def search_snopes_claim(
    claim: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    user_agent: str = "PulseNews/1.0 (+https://pulsenews.app; fact-check verification)",
    get: Optional[Callable] = None,
) -> Optional[dict]:
    """
    GET Snopes site search. WordPress default uses ?s= query on homepage.
    """
    if not claim or not claim.strip():
        return None

    q = quote_plus(claim.strip()[:500])
    url = f"{SNOPES_SEARCH}?s={q}"
    getter = get or requests.get

    try:
        resp = getter(url, timeout=timeout, headers=_default_headers(user_agent))
        if getattr(resp, "status_code", 200) != 200:
            logger.debug("Snopes search HTTP %s", getattr(resp, "status_code", "?"))
            return None
        raw = getattr(resp, "content", b"") or b""
        if len(raw) > MAX_RESPONSE_BYTES:
            raw = raw[:MAX_RESPONSE_BYTES]
        text = raw.decode("utf-8", errors="replace")
        text = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", text, flags=re.I)
        return parse_snopes_search_html(text)
    except requests.RequestException as e:
        logger.debug("Snopes search request failed: %s", e)
        return None
    except Exception as e:
        logger.debug("Snopes search unexpected error: %s", e)
        return None
