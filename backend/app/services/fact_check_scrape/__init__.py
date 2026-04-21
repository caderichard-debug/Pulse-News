"""Lightweight HTML search clients for fact-check sites (no official APIs)."""

from .politifact import search_politifact_claim
from .snopes import search_snopes_claim
from .rating_parser import parse_textual_rating_to_status

__all__ = [
    "search_politifact_claim",
    "search_snopes_claim",
    "parse_textual_rating_to_status",
]
