"""LLM provider abstraction (spec §2).

The application is NOT hard-coded around a single provider. Any provider that
implements ``LLMProvider.generate`` can be plugged in.
"""
from __future__ import annotations

import abc
import json
import re

from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMUnavailableError(RuntimeError):
    """Raised when no provider is configured or the provider call fails."""


class LLMProvider(abc.ABC):
    name = "abstract"

    @abc.abstractmethod
    async def generate(self, prompt: str) -> str:
        """Return the model's text completion for ``prompt``."""
        raise NotImplementedError

    async def generate_json(self, prompt: str, schema_model=None, max_retries: int = 3) -> dict:
        """Generate structured JSON, validate it, and retry safely on failure."""
        last_err: Exception | None = None
        raw = ""
        for attempt in range(1, max_retries + 1):
            try:
                raw = await self.generate(prompt if attempt == 1 else _repair_prompt(prompt, raw, last_err))
                data = _extract_json(raw)
                if schema_model is not None:
                    data = schema_model.model_validate(data).model_dump()
                return data
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                logger.warning("LLM JSON attempt %s/%s failed: %s", attempt, max_retries, exc)
        raise LLMUnavailableError(f"structured generation failed: {last_err}")


def _repair_prompt(original: str, previous: str, err: Exception | None) -> str:
    return (
        f"{original}\n\nYour previous answer was invalid ({err}). "
        f"Return ONLY valid minified JSON matching the requested schema. "
        f"Previous answer:\n{previous[:500]}"
    )


def _extract_json(raw: str) -> dict:
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found in response")
    return json.loads(raw[start:end + 1])
