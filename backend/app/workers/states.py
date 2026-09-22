"""Candidate processing state machine (spec §21)."""
from __future__ import annotations

from enum import Enum


class CandidateStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    EXTRACTED = "EXTRACTED"
    ANALYZED = "ANALYZED"
    SCREENED = "SCREENED"
    FAILED = "FAILED"


ALLOWED_TRANSITIONS: dict[CandidateStatus, set[CandidateStatus]] = {
    CandidateStatus.UPLOADED: {CandidateStatus.PROCESSING, CandidateStatus.FAILED},
    CandidateStatus.PROCESSING: {
        CandidateStatus.EXTRACTED,
        CandidateStatus.FAILED,
    },
    CandidateStatus.EXTRACTED: {CandidateStatus.ANALYZED, CandidateStatus.FAILED},
    CandidateStatus.ANALYZED: {CandidateStatus.SCREENED, CandidateStatus.FAILED},
    CandidateStatus.SCREENED: {CandidateStatus.PROCESSING, CandidateStatus.FAILED},
    CandidateStatus.FAILED: {CandidateStatus.PROCESSING, CandidateStatus.FAILED},
}


def can_transition(current: str, target: CandidateStatus) -> bool:
    try:
        cur = CandidateStatus(current)
    except ValueError:
        return True
    return target in ALLOWED_TRANSITIONS.get(cur, set())
