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


def enforce_auth_rate_limit(request: Request, bucket: str = "auth") -> None:
    client_ip = request.client.host if request.client else "unknown"
    key = f"{bucket}:{client_ip}"
    now = time.time()
    window_seconds = settings.auth_rate_limit_window_seconds
    max_attempts = settings.auth_rate_limit_max_attempts

    window = _windows[key].timestamps
    while window and now - window[0] > window_seconds:
        window.popleft()

    if len(window) >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please try again shortly.",
        )

    window.append(now)

