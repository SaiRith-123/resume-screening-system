"""Repositories package."""
from app.repositories.candidate_repo import CandidateRepository, ResumeRepository
from app.repositories.job_repo import JobRepository
from app.repositories.screening_repo import ScreeningRepository
from app.repositories.user_repo import UserRepository

__all__ = [
    "CandidateRepository",
    "ResumeRepository",
    "JobRepository",
    "ScreeningRepository",
    "UserRepository",
]
