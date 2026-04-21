"""
Lightweight PolitiFact search scrape (no official API).
HTML layouts change; parsing is defensive. Site policy: use sparingly, low QPS.
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

POLITIFACT_SEARCH = "https://www.politifact.com/search/"
# Avoid downloading huge pages
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


def parse_politifact_search_html(
    html: str,
    base_url: str = "https://www.politifact.com",
) -> Optional[dict]:
    """
    Parse PolitiFact search results HTML. Returns fact-check dict or None.

    Looks for factcheck article links and optional rating/snippet text.
    """
    if not html or len(html) < 200:
        return None

    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception as e:  # pragma: no cover - bs4 rarely fails
        logger.debug("PolitiFact parse soup error: %s", e)
        return None

    candidates = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        if not href or "/factchecks/" not in href.lower():
            continue
        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = base_url.rstrip("/") + href
        text = _truncate(a.get_text(" ", strip=True) or "")
        if not text or len(text) < 8:
            continue
        if href in {c[0] for c in candidates}:
            continue
        candidates.append((href, text, a))
        if len(candidates) >= MAX_CANDIDATES:
            break

    if not candidates:
        return None

    url, title, first_a = candidates[0]
    # Sniff rating from nearby text (listing cards often include meter label)
    rating_guess = ""
    parent = first_a.parent if first_a else None
    if parent:
        block = parent.get_text(" ", strip=True)
        for token in (
            "True",
            "False",
            "Mostly True",
            "Mostly False",
            "Half True",
            "Pants on Fire",
            "Mostly False",
        ):
            if token.lower() in block.lower():
                rating_guess = token
                break

    status = parse_textual_rating_to_status(rating_guess) if rating_guess else "unverifiable"
    confidence = 0.72 if rating_guess else 0.52

    return {
        "fact_check_status": status,
        "fact_check_source": "politifact_scrape",
        "fact_check_url": url,
        "fact_check_details": _truncate(f"PolitiFact: {title}" + (f" — {rating_guess}" if rating_guess else "")),
        "confidence": confidence,
    }


def search_politifact_claim(
    claim: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    user_agent: str = "PulseNews/1.0 (+https://pulsenews.app; fact-check verification)",
    get: Optional[Callable] = None,
) -> Optional[dict]:
    """
    GET PolitiFact search for claim; parse first factcheck links.

    `get` is injectable for tests (signature: get(url, **kwargs) -> object with .text, .content, .status_code).
    """
    if not claim or not claim.strip():
        return None

    q = quote_plus(claim.strip()[:500])
    url = f"{POLITIFACT_SEARCH}?q={q}"
    getter = get or requests.get

    try:
        resp = getter(
            url,
            timeout=timeout,
            headers=_default_headers(user_agent),
        )
        if getattr(resp, "status_code", 200) != 200:
            logger.debug("PolitiFact search HTTP %s", getattr(resp, "status_code", "?"))
            return None
        raw = getattr(resp, "content", b"") or b""
        if len(raw) > MAX_RESPONSE_BYTES:
            raw = raw[:MAX_RESPONSE_BYTES]
        text = raw.decode("utf-8", errors="replace")
        # Strip scripts for faster parse (optional)
        text = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", text, flags=re.I)
        return parse_politifact_search_html(text)
    except requests.RequestException as e:
        logger.debug("PolitiFact search request failed: %s", e)
        return None
    except Exception as e:
        logger.debug("PolitiFact search unexpected error: %s", e)
        return None
