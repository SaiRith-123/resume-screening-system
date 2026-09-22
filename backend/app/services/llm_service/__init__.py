"""LLM service package."""
from app.services.llm_service.genai import (
    AI_UNAVAILABLE_NOTE,
    fallback_interview_questions,
    generate_candidate_summary,
    generate_interview_questions,
    generate_screening_explanation,
)
from app.services.llm_service.provider import LLMProvider, LLMUnavailableError
from app.services.llm_service.providers import get_llm_provider

__all__ = [
    "LLMProvider",
    "LLMUnavailableError",
    "get_llm_provider",
    "generate_candidate_summary",
    "generate_screening_explanation",
    "generate_interview_questions",
    "fallback_interview_questions",
    "AI_UNAVAILABLE_NOTE",
]
