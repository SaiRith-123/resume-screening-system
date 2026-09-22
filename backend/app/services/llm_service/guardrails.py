"""LLM safety guardrails (spec §31, §32) - prompt-injection defense + output validation."""
from __future__ import annotations

import re

INJECTION_PATTERNS = [
    r"ignore (?:all |the )?(?:previous|above|prior) (?:instructions|rules|prompts)",
    r"disregard (?:all |the )?(?:previous|above) (?:instructions|rules)",
    r"you are now",
    r"rank me (?:first|top|highest|#1)",
    r"give me (?:a )?(?:perfect|maximum|highest|full) score",
    r"system prompt",
    r"reveal (?:your )?(?:instructions|prompt)",
    r"jailbreak",
    r"act as (?:a |an )?(?:different|new)",
    r"override (?:the )?(?:rules|requirements)",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

SENSITIVE_ATTRIBUTE_PATTERNS = [
    r"\bage\b", r"how old", r"\bold\b", r"\byears? old\b", r"\bgender\b", r"\bsex\b",
    r"\brace\b", r"\bethnicity\b", r"\breligion\b", r"\bmarital\b", r"\bmarried\b",
    r"\bdisabilit", r"\bnationality\b", r"\bcitizen", r"\bdate of birth\b", r"\bdob\b",
    r"\bbirth\b", r"\bphotograph\b", r"\bpregnan", r"\bchildren\b", r"\bfamily status\b",
]
_SENSITIVE = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_ATTRIBUTE_PATTERNS]


def detect_injection(text: str) -> list[str]:
    """Return the injection patterns found in untrusted text (for logging/flagging)."""
    hits = []
    for pat, rx in zip(INJECTION_PATTERNS, _COMPILED):
        if rx.search(text or ""):
            hits.append(pat)
    return hits


def sanitize_untrusted(text: str) -> str:
    """Neutralize obvious injection phrases before sending untrusted text to an LLM."""
    if not text:
        return text
    cleaned = text
    for rx in _COMPILED:
        cleaned = rx.sub("[neutralized-instruction]", cleaned)
    return cleaned


def contains_sensitive_question(question: str) -> bool:
    """True if an interview question targets a protected attribute (spec §14)."""
    return any(rx.search(question or "") for rx in _SENSITIVE)


def filter_sensitive_questions(questions: list[str]) -> list[str]:
    return [q for q in questions if not contains_sensitive_question(q)]
