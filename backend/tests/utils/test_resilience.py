"""Tests for retry and rate-limit helpers."""

import pytest
from fastapi import HTTPException

from app.utils import rate_limit
from app.utils.resilience import retry_call


def test_retry_call_returns_first_success():
    result, stats = retry_call(lambda: 42, operation="ok", backoff_base_seconds=0)
    assert result == 42
    assert stats.attempts == 1
    assert stats.failures == 0


def test_retry_call_retries_then_succeeds():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ValueError("boom")
        return "done"

    result, stats = retry_call(flaky, operation="flaky", max_retries=3, backoff_base_seconds=0)
    assert result == "done"
    assert stats.attempts == 3
    assert stats.failures == 2


def test_retry_call_reraises_after_exhaustion():
    def always_fails():
        raise ValueError("nope")

    with pytest.raises(ValueError):
        retry_call(always_fails, operation="fail", max_retries=2, backoff_base_seconds=0)


@pytest.mark.parametrize("max_retries", [0, -1])
def test_retry_call_always_attempts_once(max_retries):
    result, stats = retry_call(lambda: "x", operation="zero", max_retries=max_retries)
    assert result == "x"
    assert stats.attempts == 1


class _FakeRequest:
    def __init__(self, host="1.2.3.4"):
        self.client = type("C", (), {"host": host})()


def test_rate_limit_blocks_after_max_attempts(monkeypatch):
    monkeypatch.setattr(rate_limit.settings, "auth_rate_limit_max_attempts", 2)
    req = _FakeRequest()
    rate_limit.enforce_auth_rate_limit(req, "t")
    rate_limit.enforce_auth_rate_limit(req, "t")
    with pytest.raises(HTTPException) as exc:
        rate_limit.enforce_auth_rate_limit(req, "t")
    assert exc.value.status_code == 429
    # A different client is unaffected
    rate_limit.enforce_auth_rate_limit(_FakeRequest("5.6.7.8"), "t")


def test_rate_limit_prunes_idle_buckets(monkeypatch):
    monkeypatch.setattr(rate_limit, "_MAX_TRACKED_KEYS", 1)
    monkeypatch.setattr(rate_limit.settings, "auth_rate_limit_window_seconds", 0)
    rate_limit.enforce_auth_rate_limit(_FakeRequest("a"), "t")
    rate_limit.enforce_auth_rate_limit(_FakeRequest("b"), "t")
    rate_limit.enforce_auth_rate_limit(_FakeRequest("c"), "t")
    assert len(rate_limit._windows) <= 2
