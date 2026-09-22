"""ORM models package. Importing this module registers all tables on Base.metadata."""
from app.models.candidate import Candidate, Certification, Education, Experience, Project, Resume
from app.models.interview import InterviewQuestion
from app.models.job import Job, JobRequirement
from app.models.screening import Embedding, ScreeningEvidence, ScreeningResult
from app.models.skill import CandidateSkill, Skill
from app.models.user import User

__all__ = [
    "User",
    "Job",
    "JobRequirement",
    "Candidate",
    "Resume",
    "Experience",
    "Education",
    "Project",
    "Certification",
    "Skill",
    "CandidateSkill",
    "Embedding",
    "ScreeningResult",
    "ScreeningEvidence",
    "InterviewQuestion",
]
