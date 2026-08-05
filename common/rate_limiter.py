"""Rate Limiting Helper for Beauty Care Platform Gateways and APIs.

Enforces throttling (e.g., max 20 requests per minute per phone number or IP address)
to protect LLM Gemini quotas and defend endpoints from spam and DDOS attacks.
"""

import time
from typing import Dict, Tuple
from fastapi import HTTPException, status

_RATE_LIMIT_STORE: Dict[str, list] = {}


def check_rate_limit(client_identifier: str, max_requests: int = 20, window_seconds: int = 60) -> bool:
    """Check if client identifier exceeds allowed requests within time window.

    Args:
        client_identifier: Unique phone number, chat ID, or IP address.
        max_requests: Maximum allowed requests within window (default 20).
        window_seconds: Time window in seconds (default 60).

    Raises:
        HTTPException 429 if rate limit is exceeded.
    """
    now = time.time()
    timestamps = _RATE_LIMIT_STORE.get(client_identifier, [])

    # Filter out timestamps older than window
    valid_timestamps = [ts for ts in timestamps if now - ts < window_seconds]

    if len(valid_timestamps) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded ({max_requests} req/{window_seconds}s). Please slow down.",
        )

    valid_timestamps.append(now)
    _RATE_LIMIT_STORE[client_identifier] = valid_timestamps
    return True


class SlidingWindowRateLimiter:
    """Sliding Window Rate Limiter for test and modular use."""

    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        self.store: Dict[str, list] = {}

    def is_allowed(self, client_identifier: str) -> bool:
        """Check if request from client is allowed."""
        now = time.time()
        timestamps = self.store.get(client_identifier, [])
        valid_timestamps = [ts for ts in timestamps if now - ts < self.window_seconds]
        if len(valid_timestamps) >= self.requests_per_minute:
            return False
        valid_timestamps.append(now)
        self.store[client_identifier] = valid_timestamps
        return True

