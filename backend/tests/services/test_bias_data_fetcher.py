"""
Tests for bias data fetcher service.
"""

import pytest
from app.services.bias_data_fetcher import (
    extract_domain,
    map_bias_string_to_enum,
    fetch_source_bias,
    get_bias_for_source
)
from app.models import OrganizationalBias


def test_extract_domain_with_www():
    """Test domain extraction removes www prefix."""
    url = "https://www.nytimes.com/article"
    domain = extract_domain(url)
    assert domain == "nytimes.com"


def test_extract_domain_with_subdomain():
    """Test domain extraction handles subdomains."""
    url = "https://news.bbc.co.uk/article"
    domain = extract_domain(url)
    assert domain == "news.bbc.co.uk"


def test_extract_domain_simple():
    """Test domain extraction with simple domain."""
    url = "https://reuters.com/news"
    domain = extract_domain(url)
    assert domain == "reuters.com"


def test_extract_domain_no_protocol():
    """Test domain extraction without protocol."""
    url = "npr.org"
    domain = extract_domain(url)
    assert domain == "npr.org"


def test_map_bias_string_left():
    """Test mapping left bias strings."""
    assert map_bias_string_to_enum("left") == OrganizationalBias.LEFT
    assert map_bias_string_to_enum("LEFT") == OrganizationalBias.LEFT
    assert map_bias_string_to_enum("extreme left") == OrganizationalBias.LEFT


def test_map_bias_string_center_left():
    """Test mapping center-left bias strings."""
    assert map_bias_string_to_enum("lean left") == OrganizationalBias.CENTER_LEFT
    assert map_bias_string_to_enum("left-center") == OrganizationalBias.CENTER_LEFT
    assert map_bias_string_to_enum("center-left") == OrganizationalBias.CENTER_LEFT


def test_map_bias_string_center():
    """Test mapping center bias strings."""
    assert map_bias_string_to_enum("center") == OrganizationalBias.CENTER
    assert map_bias_string_to_enum("CENTER") == OrganizationalBias.CENTER
    assert map_bias_string_to_enum("least biased") == OrganizationalBias.CENTER
    assert map_bias_string_to_enum("mixed") == OrganizationalBias.CENTER


def test_map_bias_string_center_right():
    """Test mapping center-right bias strings."""
    assert map_bias_string_to_enum("lean right") == OrganizationalBias.CENTER_RIGHT
    assert map_bias_string_to_enum("right-center") == OrganizationalBias.CENTER_RIGHT
    assert map_bias_string_to_enum("center-right") == OrganizationalBias.CENTER_RIGHT


def test_map_bias_string_right():
    """Test mapping right bias strings."""
    assert map_bias_string_to_enum("right") == OrganizationalBias.RIGHT
    assert map_bias_string_to_enum("RIGHT") == OrganizationalBias.RIGHT
    assert map_bias_string_to_enum("extreme right") == OrganizationalBias.RIGHT


def test_map_bias_string_case_insensitive():
    """Test that bias mapping is case insensitive."""
    assert map_bias_string_to_enum("LeFt") == OrganizationalBias.LEFT
    assert map_bias_string_to_enum("CeNtEr") == OrganizationalBias.CENTER
    assert map_bias_string_to_enum("RiGhT") == OrganizationalBias.RIGHT


def test_map_bias_string_unknown():
    """Test that unknown strings return None."""
    assert map_bias_string_to_enum("unknown") is None
    assert map_bias_string_to_enum("") is None
    assert map_bias_string_to_enum("random") is None


@pytest.mark.asyncio
async def test_fetch_source_bias_known_source():
    """Test fetching bias for known source."""
    result = await fetch_source_bias("https://npr.org")

    assert result["bias"] == OrganizationalBias.CENTER_LEFT
    assert result["description"] is not None
    assert result["confidence"] > 0
    assert result["method"] == "manual_lookup"


@pytest.mark.asyncio
async def test_fetch_source_bias_ap():
    """Test AP News is center."""
    result = await fetch_source_bias("https://apnews.com")

    assert result["bias"] == OrganizationalBias.CENTER
    assert "wire service" in result["description"].lower()


@pytest.mark.asyncio
async def test_fetch_source_bias_nytimes():
    """Test NYT is center-left."""
    result = await fetch_source_bias("https://nytimes.com")

    assert result["bias"] == OrganizationalBias.CENTER_LEFT
    assert result["confidence"] >= 0.85


@pytest.mark.asyncio
async def test_fetch_source_bias_foxnews():
    """Test Fox News is right."""
    result = await fetch_source_bias("https://foxnews.com")

    assert result["bias"] == OrganizationalBias.RIGHT
    assert result["confidence"] >= 0.90


@pytest.mark.asyncio
async def test_fetch_source_bias_unknown_source():
    """Test handling of unknown source."""
    result = await fetch_source_bias("https://unknownsource12345.com")

    assert result["bias"] is None
    assert result["confidence"] == 0.0
    assert result["method"] == "unknown"
    assert "not yet available" in result["description"]


@pytest.mark.asyncio
async def test_fetch_source_bias_with_www():
    """Test that www prefix is handled correctly."""
    result = await fetch_source_bias("https://www.npr.org")

    assert result["bias"] == OrganizationalBias.CENTER_LEFT
    assert result["method"] == "manual_lookup"


@pytest.mark.asyncio
async def test_get_bias_for_source_simple():
    """Test simplified interface."""
    bias, description = await get_bias_for_source("https://reuters.com")

    assert bias == OrganizationalBias.CENTER
    assert description is not None
    assert len(description) > 0


@pytest.mark.asyncio
async def test_get_bias_for_source_unknown():
    """Test simplified interface with unknown source."""
    bias, description = await get_bias_for_source("https://unknown999.com")

    assert bias is None
    assert description is not None
