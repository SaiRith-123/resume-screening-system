"""Skill normalization (spec §7)."""
from __future__ import annotations

import re

from app.services.skill_matcher.taxonomy import ALIAS_TO_CANONICAL

_PAREN = re.compile(r"\([^)]*\)")
_NOISE = re.compile(
    r"\b(experience|experienced|expert|proficient|advanced|basic|intermediate|"
    r"knowledge|skilled|development|developer|framework|library|technologies|technology)\b",
    re.IGNORECASE,
)
_MULTISPACE = re.compile(r"\s+")


def _clean(name: str) -> str:
    s = name.strip().strip(".,;:|-•·")
    s = s.replace("&", " and ")
    s = _PAREN.sub(" ", s)
    s = _NOISE.sub(" ", s)
    s = _MULTISPACE.sub(" ", s).strip().lower()
    return s


def normalize_skill(name: str) -> str:
    """Map a raw skill string to its canonical name (or a cleaned fallback)."""
    if not name:
        return ""
    cleaned = _clean(name)
    if not cleaned:
        return ""
    if cleaned in ALIAS_TO_CANONICAL:
        return ALIAS_TO_CANONICAL[cleaned]
    # try without punctuation / with compact form (Node.JS -> nodejs)
    compact = re.sub(r"[^a-z0-9+#]", "", cleaned)
    for alias, canon in ALIAS_TO_CANONICAL.items():
        if re.sub(r"[^a-z0-9+#]", "", alias) == compact:
            return canon
    # Not in taxonomy: keep a title-cased cleaned form so distinct skills stay distinct
    return cleaned.title()


def normalize_skills(names: list[str]) -> list[str]:
    """Normalize and de-duplicate a list of skill names, preserving order."""
    seen: set[str] = set()
    out: list[str] = []
    for n in names or []:
        c = normalize_skill(n)
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out
