"""
Map textual fact-check ratings to Pulse status codes.
Shared by Google Fact Check integration and HTML scrapers.
"""


def parse_textual_rating_to_status(rating_text: str) -> str:
    """
    Parse a textual rating into: verified | false | mixed | unverifiable.

    Handles PolitiFact, Snopes, Google, and common variants.
    """
    if not rating_text:
        return "unverifiable"

    rating_lower = rating_text.lower()

    if any(word in rating_lower for word in ["false", "incorrect", "inaccurate", "pants on fire"]):
        if any(word in rating_lower for word in ["mostly"]):
            return "mixed"
        return "false"

    if any(word in rating_lower for word in ["mixture", "mixed", "half"]):
        return "mixed"

    if any(word in rating_lower for word in ["true", "correct", "accurate"]):
        if any(word in rating_lower for word in ["mostly", "partially"]):
            return "mixed"
        return "verified"

    if any(word in rating_lower for word in ["unproven", "unclear", "unsupported", "undetermined"]):
        return "unverifiable"

    return "unverifiable"


_RATING_CLASS_HINTS = ("meter", "rating", "verdict", "ruling")


def guess_rating_near(anchor, tokens, max_levels: int = 3) -> str:
    """
    Find a rating label (e.g. "Mostly True") near a search-result link.

    Looks first at elements whose class suggests a rating, then at surrounding
    text, walking up a few ancestor levels. The link's own text (the headline) is
    ignored, since headlines often contain words like "false" or "true".
    Tokens are matched most-specific first with word boundaries, so "Mostly True"
    is never reported as "True".
    """
    import re

    ordered = sorted(tokens, key=len, reverse=True)
    patterns = [(t, re.compile(rf"\b{re.escape(t)}\b", re.IGNORECASE)) for t in ordered]
    headline = anchor.get_text(" ", strip=True) if anchor is not None else ""

    def match(text: str) -> str:
        for token, pattern in patterns:
            if pattern.search(text):
                return token
        return ""

    node = anchor
    for _ in range(max_levels):
        node = getattr(node, "parent", None)
        if node is None:
            break
        for el in node.find_all(class_=True):
            classes = " ".join(el.get("class") or []).lower()
            if any(h in classes for h in _RATING_CLASS_HINTS):
                found = match(el.get_text(" ", strip=True))
                if found:
                    return found
        text = node.get_text(" ", strip=True)
        if headline:
            text = text.replace(headline, " ")
        found = match(text)
        if found:
            return found
    return ""
