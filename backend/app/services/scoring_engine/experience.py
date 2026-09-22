"""Experience calculation (spec §11).

Merges overlapping employment intervals, excludes academic projects from
professional experience, handles current / partial / missing dates.
"""
from __future__ import annotations

import re
from datetime import date, datetime

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}

PROFESSIONAL_KINDS = {"full-time", "freelance", "internship", "contract"}
_ACADEMIC_HINTS = ("university", "college", "academic", "coursework", "capstone")


def _to_date(value: str | None) -> date | None:
    if not value:
        return None
    v = str(value).strip().lower()
    if v in {"present", "current", "now", ""}:
        return None
    m = re.match(r"^([a-z]{3,9})\.?\s*(\d{4})$", v)
    if m and m.group(1)[:3] in MONTHS:
        return date(int(m.group(2)), MONTHS[m.group(1)[:3]], 1)
    m = re.match(r"^(\d{4})$", v)
    if m:
        return date(int(m.group(1)), 1, 1)
    m = re.match(r"^(\d{4})[-/](\d{1,2})$", v)
    if m:
        return date(int(m.group(1)), int(m.group(2)), 1)
    try:
        return datetime.fromisoformat(str(value)).date()
    except Exception:
        return None


def _months_between(start: date, end: date) -> float:
    return max(0.0, (end.year - start.year) * 12 + (end.month - start.month))


def classify_kind(exp: dict) -> str:
    kind = (exp.get("kind") or "").lower()
    if kind in PROFESSIONAL_KINDS:
        return kind
    text = f"{exp.get('company', '')} {exp.get('title', '')} {exp.get('description', '')}".lower()
    if "intern" in text:
        return "internship"
    if "freelance" in text or "freelancing" in text:
        return "freelance"
    if any(h in text for h in _ACADEMIC_HINTS):
        return "academic"
    return "full-time"


def experience_intervals(experiences: list[dict]) -> list[tuple[date, date]]:
    """Return merged, professional-only intervals (spec §11 overlap handling)."""
    today = date.today()
    raw: list[tuple[date, date]] = []
    for exp in experiences or []:
        kind = classify_kind(exp)
        if kind == "academic":
            continue  # never count academic projects as professional experience
        start = _to_date(exp.get("start_date"))
        end = _to_date(exp.get("end_date"))
        if start is None and end is None:
            continue  # undated -> cannot count reliably
        if start is None:
            start = end  # partial date: assume ~1 month
        if end is None:
            end = today if exp.get("is_current") else start
        if end < start:
            start, end = end, start
        # require at least a month of span OR explicitly current
        if _months_between(start, end) <= 0 and not exp.get("is_current"):
            continue
        raw.append((start, end))
    return _merge_intervals(raw)


def _merge_intervals(intervals: list[tuple[date, date]]) -> list[tuple[date, date]]:
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda x: x[0])
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def total_experience_years(experiences: list[dict]) -> float:
    merged = experience_intervals(experiences)
    months = sum(_months_between(s, e) for s, e in merged)
    return round(months / 12.0, 1)


def experience_score(
    candidate_years: float, minimum_years: float | None, preferred_years: float | None = None
) -> float:
    """0..100 experience-match score with smooth partial credit (spec §10, §11)."""
    if not minimum_years or minimum_years <= 0:
        return 100.0 if candidate_years > 0 else 60.0
    ratio = candidate_years / minimum_years
    if ratio >= 1.5:
        return 100.0
    if ratio >= 1.0:
        return round(85.0 + (ratio - 1.0) / 0.5 * 15.0, 1)
    if ratio >= 0.5:
        return round(45.0 + (ratio - 0.5) / 0.5 * 40.0, 1)
    return round(max(0.0, ratio * 90.0), 1)
