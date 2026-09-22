"""ASGI middlewares: request IDs + access logs, security headers."""
from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.logging import get_logger
from app.core.llm_context import openai_api_key

logger = get_logger("access")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assigns a request id, logs method/path/status/latency, echoes headers."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        key = request.headers.get("x-openai-api-key")
        token = openai_api_key.set(key.strip() if key and key.strip() else None)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            openai_api_key.reset(token)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.1f}"
        logger.info(
            '%s %s -> %s (%.1f ms) [%s]',
            request.method, request.url.path, response.status_code, elapsed_ms, request_id,
        )
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Baseline hardening headers on every response.

    A strict Content-Security-Policy is intentionally NOT set here because the
    API serves Swagger UI (/docs); deploy a CSP at the proxy/CDN layer for the
    frontend (see SECURITY.md).
    """

    HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "Cross-Origin-Opener-Policy": "same-origin",
    }

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for key, value in self.HEADERS.items():
            response.headers.setdefault(key, value)
        return response
