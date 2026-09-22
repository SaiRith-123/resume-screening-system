"""Aggregate the v1 API router."""
from fastapi import APIRouter

from app.api.v1 import auth, candidates, export, jobs, resumes, search

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(jobs.router)
api_router.include_router(resumes.router)
api_router.include_router(candidates.router)
api_router.include_router(search.router)
api_router.include_router(export.router)
