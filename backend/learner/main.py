import os
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, Path as PathParam, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from backend.agent.schemas import (
    AttemptRecordRequest,
    AttemptRecordResponse,
    MasteryResponse,
    WeakConceptsResponse,
    RecommendResponse,
)
from backend.learner.service import learner_service
from backend.learner.seed import seed_demo_data

app = FastAPI(
    title="Learner Model Service & Student Knowledge Graph",
    description="Maintains student mastery profiles via EWMA with temporal forgetting decay, active misconception catalogs, and pedagogical recommendations.",
    version="1.0.0",
)

# Enable CORS for frontend dashboard and cross-service communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check for learner service."""
    return {
        "status": "healthy",
        "service": "backend/learner",
        "engine": "EWMA + Ebbinghaus Decay",
        "storage": "SQLite",
    }


@app.post(
    "/learner/attempt",
    response_model=AttemptRecordResponse,
    tags=["Learner Model"],
    summary="Record a student answer or exercise attempt"
)
async def record_attempt(req: AttemptRecordRequest):
    """
    Record an attempt on a question or exercise.
    Updates the exponentially weighted mastery score and logs misconceptions.
    """
    try:
        return learner_service.record_attempt(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record attempt: {str(e)}")


@app.get(
    "/learner/mastery/{user_id}",
    response_model=MasteryResponse,
    tags=["Learner Model"],
    summary="Get mastery scores for all concepts"
)
async def get_mastery(
    user_id: str = PathParam(..., description="Student ID", examples=["demo_student"])
):
    """Returns overall mastery and per-concept scores (0.0 to 1.0)."""
    try:
        return learner_service.get_mastery(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get mastery: {str(e)}")


@app.get(
    "/learner/weak/{user_id}",
    response_model=WeakConceptsResponse,
    tags=["Learner Model"],
    summary="Get weak concepts needing practice"
)
async def get_weak_concepts(
    user_id: str = PathParam(..., description="Student ID", examples=["demo_student"])
):
    """Returns list of weak concepts (mastery < 0.60) and active misconceptions."""
    try:
        return learner_service.get_weak_concepts(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get weak concepts: {str(e)}")


@app.get(
    "/learner/recommend/{user_id}",
    response_model=RecommendResponse,
    tags=["Learner Model"],
    summary="Get next recommended topic or lesson"
)
async def get_recommendation(
    user_id: str = PathParam(..., description="Student ID", examples=["demo_student"])
):
    """Returns the highest priority concept recommendation and suggested action."""
    try:
        return learner_service.recommend_next(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendation: {str(e)}")


@app.get("/learner/history/{user_id}", tags=["Learner Analytics"], summary="Get recent practice attempt history")
async def get_history(
    user_id: str = PathParam(..., description="Student ID"),
    limit: int = Query(default=20, ge=1, le=100)
):
    """Returns chronological attempt logs with time spent and misconception tags."""
    return learner_service.get_history(user_id, limit=limit)


@app.get("/learner/summary/{user_id}", tags=["Learner Analytics"], summary="Full student profile snapshot for dashboard")
async def get_summary(user_id: str = PathParam(..., description="Student ID")):
    """Returns aggregate student analytics snapshot for real-time dashboard rendering."""
    return learner_service.get_user_summary(user_id)


@app.post("/learner/seed", tags=["Admin"], summary="Reset and reseed demo student database")
async def reset_seed():
    """Resets the demo student database to initial pitch demo state."""
    seed_demo_data()
    return {"status": "success", "message": "Demo student data reset to benchmark scenario."}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("LEARNER_PORT", 8002))
    uvicorn.run("backend.learner.main:app", host="0.0.0.0", port=port, reload=True)
