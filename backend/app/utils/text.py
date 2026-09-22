"""Text helpers."""
from __future__ import annotations

import re

_WS = re.compile(r"[ \t]+")
_BLANKS = re.compile(r"\n{3,}")


def clean_text(text: str) -> str:
    if not text:
        return ""
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = _WS.sub(" ", t)
    t = _BLANKS.sub("\n\n", t)
    return t.strip()


def truncate(text: str, limit: int = 4000) -> str:
    return text if len(text) <= limit else text[:limit] + "…"
