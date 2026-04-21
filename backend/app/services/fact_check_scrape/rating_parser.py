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
