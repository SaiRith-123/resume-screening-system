"""Resume section detection (spec §5)."""
from __future__ import annotations

import re

SECTION_ALIASES: dict[str, list[str]] = {
    "summary": ["summary", "professional summary", "profile", "objective", "about me",
                "career objective", "professional profile"],
    "skills": ["skills", "technical skills", "core competencies", "technologies",
               "technical proficiencies", "skill set", "areas of expertise"],
    "experience": ["experience", "work experience", "professional experience",
                   "employment history", "work history", "professional background"],
    "education": ["education", "academic background", "academics",
                  "educational qualifications", "qualifications"],
    "projects": ["projects", "personal projects", "academic projects",
                 "key projects", "selected projects"],
    "certifications": ["certifications", "certificates", "licenses",
                       "professional certifications", "certifications and licenses"],
    "contact": ["contact", "contact information", "personal details"],
    "languages": ["languages", "language proficiency"],
    "awards": ["awards", "achievements", "honors", "accomplishments"],
}

# Compile a heading matcher: line that is mostly a known heading.
_HEADING_RE = re.compile(r"^[A-Z][A-Za-z /&+-]{2,40}:?$")


def _match_heading(line: str) -> str | None:
    raw = line.strip()
    # strip markdown heading markers and bullets (## Skills, - Skills:, • Education)
    raw = raw.lstrip("#").strip().lstrip("-*•·").strip().strip(":").strip()
    if not raw or len(raw) > 45:
        return None
    lower = raw.lower()
    for section, aliases in SECTION_ALIASES.items():
        if lower in aliases:
            return section
    # allow "Skills & Tools" style
    for section, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            if lower.startswith(alias) and len(lower) <= len(alias) + 12:
                return section
    return None


def detect_sections(text: str) -> dict[str, str]:
    """Split resume text into a mapping of section -> body text."""
    lines = (text or "").splitlines()
    sections: dict[str, list[str]] = {}
    current = "header"
    for line in lines:
        heading = _match_heading(line)
        if heading:
            current = heading
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items()}
