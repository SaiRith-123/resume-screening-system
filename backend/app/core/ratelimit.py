"""In-process sliding-window rate limiting (no external dependency).

Used to protect authentication endpoints from brute-force attempts. Limits are
configured via settings (RATE_LIMIT_AUTH / RATE_LIMIT_DEFAULT) as "N/unit"
strings with unit in {second, minute, hour}.
"""
from __future__ import annotations

import math
import time
from collections import defaultdict, deque
from functools import wraps

from fastapi import HTTPException, Request, status

from app.core.config import settings

_UNITS = {"second": 1, "minute": 60, "hour": 3600}

# key -> deque[timestamps]
_buckets: dict[str, deque[float]] = defaultdict(deque)


def parse_limit(limit: str) -> tuple[int, int]:
    """Parse '20/minute' -> (20, 60). Raises ValueError on bad input."""
    try:
        count_s, unit = limit.strip().lower().split("/")
        count = int(count_s)
        window = _UNITS[unit.rstrip("s")]
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"invalid rate limit string: {limit!r}") from exc
    if count <= 0:
        raise ValueError("rate limit count must be positive")
    return count, window


def _client_key(request: Request) -> str:
    host = request.client.host if request.client else "anonymous"
    forwarded = request.headers.get("x-forwarded-for")
    return (forwarded.split(",")[0].strip() if forwarded else host) or "anonymous"


def _hit(key: str, count: int, window: int) -> float | None:
    """Record a hit; return seconds until retry when the limit is exceeded."""
    now = time.monotonic()
    bucket = _buckets[key]
    cutoff = now - window
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    if len(bucket) >= count:
        return max(1.0, math.ceil(bucket[0] + window - now))
    bucket.append(now)
    return None


def rate_limit(bucket: str):
    """Dependency factory: rate-limit a route by client IP within `bucket`."""

    def dependency(request: Request) -> None:
        limit_str = (
            getattr(settings, f"RATE_LIMIT_{bucket.upper()}", "") or settings.RATE_LIMIT_DEFAULT
        )
        count, window = parse_limit(limit_str)
        retry_after = _hit(f"{bucket}:{_client_key(request)}", count, window)
        if retry_after is not None:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down.",
                headers={"Retry-After": str(int(retry_after))},
            )

    wraps(dependency)
    return dependency


def reset_buckets() -> None:
    """Test helper: clear all recorded hits."""
    _buckets.clear()
