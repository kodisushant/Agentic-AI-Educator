"""
Backend Assessment Module.
Provides topic-specific quiz generation, flashcards, evaluation,
and integration with the learner model.
"""

from backend.assess.service import AssessmentService, assess_service
from backend.assess.router import assess_router

__all__ = ["AssessmentService", "assess_service", "assess_router"]

