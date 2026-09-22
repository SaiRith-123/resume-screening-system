"""Evidence extraction - every important match carries grounded evidence (spec §13).

Evidence text MUST be a real substring of the resume. Anything the LLM produces
is validated against the source text and dropped if ungrounded.
"""
from __future__ import annotations

import re

_SENT_SPLIT = re.compile(r"(?<=[.!?\n])\s+")


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text or "") if s.strip()]


def find_evidence(skill: str, text: str, context: str | None = None, max_len: int = 240) -> str | None:
    """Return the most relevant resume sentence containing the skill, or None."""
    if not text or not skill:
        return None
    needles = [skill.lower()] + [p.lower() for p in re.split(r"[\s./-]+", skill) if len(p) > 2]
    best: tuple[int, str] | None = None
    for sent in _sentences(text):
        low = sent.lower()
        if any(n in low for n in needles):
            score = sum(low.count(n) for n in needles)
            # prefer experience/project sections if the sentence is longer/descriptive
            if len(sent) > 25:
                score += 1
            cand = sent[:max_len]
            if best is None or score > best[0]:
                best = (score, cand)
    return best[1] if best else None


def is_grounded(evidence: str, source_text: str) -> bool:
    """True if the evidence is (approximately) contained in the source text."""
    if not evidence or not source_text:
        return False
    norm = lambda s: re.sub(r"\s+", " ", s.lower()).strip()
    return norm(evidence) in norm(source_text)


def filter_grounded(items: list[str], source_text: str) -> list[str]:
    return [e for e in items if is_grounded(e, source_text)]
