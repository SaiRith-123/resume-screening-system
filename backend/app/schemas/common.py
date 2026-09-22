"""Shared/common schemas and the status enums used across the API."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class MatchStatus(str, Enum):
    MATCH = "MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"


class RequirementKind(str, Enum):
    SKILL = "skill"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    CERTIFICATION = "certification"
    TECHNOLOGY = "technology"


class RequirementPriority(str, Enum):
    REQUIRED = "required"
    PREFERRED = "preferred"


class MessageOut(BaseModel):
    message: str


class Paginated(BaseModel):
    total: int
    page: int
    page_size: int
    items: list
