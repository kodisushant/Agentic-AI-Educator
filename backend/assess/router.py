"""
FastAPI Router for Assessment Engine (/assess).
Implements contracts defined in /contracts/openapi.json.
"""

from fastapi import APIRouter, HTTPException
from backend.agent.schemas import (
    QuizGenerateRequest,
    QuizGenerateResponse,
    FlashcardsGenerateRequest,
    FlashcardsGenerateResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
)
from backend.assess.service import assess_service

assess_router = APIRouter(prefix="/assess", tags=["Assessment"])


@assess_router.get("/health")
async def assess_health():
    """Health check for assessment module."""
    return {
        "status": "healthy",
        "service": "backend/assess",
        "active_quizzes_cached": len(assess_service.active_quizzes),
    }


@assess_router.post(
    "/quiz",
    response_model=QuizGenerateResponse,
    summary="Generate a topic-specific quiz"
)
async def generate_quiz_endpoint(req: QuizGenerateRequest):
    """Generates an MCQ quiz targeted to specified topic and weak concepts."""
    try:
        return await assess_service.generate_quiz(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")


@assess_router.post(
    "/flashcards",
    response_model=FlashcardsGenerateResponse,
    summary="Generate flashcards for spaced repetition"
)
async def generate_flashcards_endpoint(req: FlashcardsGenerateRequest):
    """Generates prompt/answer flashcard pairs for memory reinforcement."""
    try:
        return await assess_service.generate_flashcards(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate flashcards: {str(e)}")


@assess_router.post(
    "/submit",
    response_model=QuizSubmitResponse,
    summary="Submit quiz responses and evaluate"
)
async def submit_quiz_endpoint(req: QuizSubmitRequest):
    """
    Evaluates student quiz submissions, computes score, generates question feedback,
    and publishes attempts to the learner mastery model.
    """
    try:
        return assess_service.submit_quiz(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate quiz submission: {str(e)}")

