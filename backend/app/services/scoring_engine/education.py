"""Education matching (spec §12).

Institution prestige is NEVER scored unless the recruiter explicitly configures it.
"""
from __future__ import annotations

import re

# degree level ranking
LEVELS = {
    "phd": 5, "doctorate": 5, "doctor": 5,
    "master": 4, "m.tech": 4, "mtech": 4, "m.sc": 4, "msc": 4, "mba": 4, "m.s": 4, "m.e": 4,
    "bachelor": 3, "b.tech": 3, "btech": 3, "b.e": 3, "bsc": 3, "b.sc": 3, "bca": 3, "b.a": 3,
    "diploma": 2, "associate": 2, "high school": 1,
}
FIELD_SYNONYMS = {
    "computer science": ["cs", "cse", "computers", "computing"],
    "information technology": ["it", "information systems"],
    "data science": ["data analytics", "analytics"],
    "artificial intelligence": ["ai", "machine learning"],
    "electrical engineering": ["eee", "electrical"],
    "electronics": ["ece", "electronics engineering"],
    "business": ["commerce", "management", "bcom"],
}

_canonical = {
    "computer science": "Computer Science",
    "information technology": "Information Technology",
    "data science": "Data Science",
    "artificial intelligence": "Artificial Intelligence",
    "electrical engineering": "Electrical Engineering",
    "electronics": "Electronics",
    "business": "Business",
    "mathematics": "Mathematics",
    "statistics": "Statistics",
}


def _level(text: str) -> int:
    low = text.lower()
    best = 0
    for key, lvl in LEVELS.items():
        if re.search(r"(?<![a-z])" + re.escape(key) + r"(?![a-z])", low):
            best = max(best, lvl)
    return best


def _field(text: str) -> str | None:
    low = text.lower()
    for canon, syns in FIELD_SYNONYMS.items():
        if canon in low or any(re.search(r"(?<![a-z])" + re.escape(s) + r"(?![a-z])", low)
                               for s in syns):
            return _canonical.get(canon, canon.title())
    return None


def match_education(candidate_education: list[dict], required: list[str]) -> tuple[str, float]:
    """Return (status, score 0..100). status in MATCH/PARTIAL_MATCH/MISSING/UNKNOWN."""
    if not required:
        return "UNKNOWN", 100.0
    if not candidate_education:
        return "MISSING", 0.0
    req_level = max((_level(r) for r in required), default=0)
    req_field = next((_field(r) for r in required if _field(r)), None)
    best = 0.0
    best_status = "MISSING"
    for edu in candidate_education:
        blob = " ".join(str(edu.get(k, "")) for k in ("degree", "field_of_study", "institution"))
        cand_level = _level(blob)
        cand_field = _field(blob)
        if req_level and cand_level >= req_level:
            level_ok, base = True, 90.0
        elif req_level and cand_level == req_level - 1:
            level_ok, base = False, 55.0
        elif req_level and cand_level > 0:
            level_ok, base = False, 35.0
        else:
            level_ok, base = True, 70.0
        if req_field:
            if cand_field == req_field:
                base = min(100.0, base + 10.0)
            elif cand_field is not None:
                base = base * 0.85
            else:
                base = base * 0.75
        if level_ok and (req_field is None or cand_field == req_field):
            status = "MATCH"
        elif base >= 45:
            status = "PARTIAL_MATCH"
        else:
            status = "MISSING"
        if base > best:
            best = base
            best_status = status
    return best_status, round(best, 1)
