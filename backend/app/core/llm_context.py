"""Request-scoped LLM credentials; values are never persisted."""
from __future__ import annotations

from contextvars import ContextVar


openai_api_key: ContextVar[str | None] = ContextVar("openai_api_key", default=None)