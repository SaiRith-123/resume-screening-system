"""Schema package.

Note: ``app.schemas.auth`` declares ``EmailStr`` fields, which require the
``email-validator`` package at import time. It is listed in every requirements
file; the guard below turns a partial install into a clear, actionable message
instead of a deep pydantic traceback.
"""
try:
    from app.schemas.auth import FirebaseLogin, Token, UserLogin, UserOut, UserRegister
except ImportError as exc:  # pragma: no cover - only on incomplete installs
    if "email" in str(exc).lower():
        raise ImportError(
            "Missing dependency: email-validator. Install it with:\n"
            "    pip install email-validator\n"
            "(it is required by the EmailStr fields in app/schemas/auth.py)"
        ) from exc
    raise

from app.schemas.candidate import (
    CandidateDetail,
    CandidateListItem,
    EvidenceOut,
    GenAIExplanation,
    InterviewQuestionOut,
    InterviewQuestionsOut,
    ScoreBreakdown,
    ScreeningResultOut,
    SkillMatchOut,
)
from app.schemas.common import MatchStatus, MessageOut, Paginated, RequirementKind
from app.schemas.job import (
    JobCreate,
    JobListItem,
    JobOut,
    JobRequirementsSchema,
    JobUpdate,
    RequirementIn,
    RequirementOut,
    ScoringWeights,
)
from app.schemas.resume import ResumeSchema

__all__ = [
    "FirebaseLogin", "Token", "UserLogin", "UserOut", "UserRegister",
    "CandidateDetail", "CandidateListItem", "EvidenceOut", "GenAIExplanation",
    "InterviewQuestionOut", "InterviewQuestionsOut", "ScoreBreakdown",
    "ScreeningResultOut", "SkillMatchOut",
    "MatchStatus", "MessageOut", "Paginated", "RequirementKind",
    "JobCreate", "JobListItem", "JobOut", "JobRequirementsSchema", "JobUpdate",
    "RequirementIn", "RequirementOut", "ScoringWeights", "ResumeSchema",
]
