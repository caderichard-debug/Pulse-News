"""Tests for lightweight fact-check HTML parsers (offline fixtures)."""

from pathlib import Path

import pytest

from app.services.fact_check_scrape.politifact import parse_politifact_search_html, search_politifact_claim
from app.services.fact_check_scrape.snopes import parse_snopes_search_html, search_snopes_claim
from app.services.fact_check_scrape.rating_parser import parse_textual_rating_to_status

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "fact_check"


def test_parse_textual_rating():
    assert parse_textual_rating_to_status("Pants on Fire") == "false"
    assert parse_textual_rating_to_status("Mostly True") == "mixed"
    assert parse_textual_rating_to_status("True") == "verified"
    assert parse_textual_rating_to_status("") == "unverifiable"


def test_parse_politifact_fixture():
    html = (FIXTURES / "politifact_search_sample.html").read_text()
    out = parse_politifact_search_html(html)
    assert out is not None
    assert out["fact_check_source"] == "politifact_scrape"
    assert "/factchecks/" in out["fact_check_url"]
    assert out["fact_check_status"] == "mixed"  # Mostly True
    assert out["confidence"] >= 0.5


def test_parse_snopes_fixture():
    html = (FIXTURES / "snopes_search_sample.html").read_text()
    out = parse_snopes_search_html(html)
    assert out is not None
    assert out["fact_check_source"] == "snopes_scrape"
    assert "/fact-check/" in out["fact_check_url"]
    assert out["fact_check_status"] == "false"


def test_politifact_search_uses_injected_get():
    html = (FIXTURES / "politifact_search_sample.html").read_text()

    class Resp:
        status_code = 200
        content = html.encode()

    def fake_get(url, **kwargs):
        assert "politifact.com/search" in url
        return Resp()

    out = search_politifact_claim("test inflation", get=fake_get)
    assert out is not None
    assert out["fact_check_source"] == "politifact_scrape"


def test_snopes_search_uses_injected_get():
    html = (FIXTURES / "snopes_search_sample.html").read_text()

    class Resp:
        status_code = 200
        content = html.encode()

    def fake_get(url, **kwargs):
        assert "snopes.com" in url
        assert "s=" in url
        return Resp()

    out = search_snopes_claim("viral claim", get=fake_get)
    assert out is not None
    assert out["fact_check_source"] == "snopes_scrape"
