import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict

from fastapi import HTTPException, Request, status

from ..config import settings


@dataclass
class _RateWindow:
    timestamps: Deque[float]


_windows: Dict[str, _RateWindow] = defaultdict(lambda: _RateWindow(deque()))


_MAX_TRACKED_KEYS = 10_000


def _prune(now: float, window_seconds: int) -> None:
    stale = [
        k for k, w in _windows.items()
        if not w.timestamps or now - w.timestamps[-1] > window_seconds
    ]
    for k in stale:
        del _windows[k]


def reset_rate_limits() -> None:
    """Clear all rate-limit state (used by tests)."""
    _windows.clear()


def enforce_auth_rate_limit(request: Request, bucket: str = "auth") -> None:
    client_ip = request.client.host if request.client else "unknown"
    key = f"{bucket}:{client_ip}"
    now = time.time()
    window_seconds = settings.auth_rate_limit_window_seconds
    max_attempts = settings.auth_rate_limit_max_attempts

    window = _windows[key].timestamps
    while window and now - window[0] > window_seconds:
        window.popleft()

    # Opportunistically drop idle buckets so the dict doesn't grow without bound.
    if len(_windows) > _MAX_TRACKED_KEYS:
        _prune(now, window_seconds)

    if len(window) >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please try again shortly.",
        )

    window.append(now)

