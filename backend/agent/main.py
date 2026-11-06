import asyncio
import logging
from contextlib import asynccontextmanager
import json
import os
from typing import AsyncGenerator, List
from fastapi import FastAPI, HTTPException, Path as PathParam, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.agent.schemas import (
    LessonStep,
    LessonStepRequest,
    ChatMessageRequest,
    ChatMessageResponse,
    ToolCallRequest,
    ToolCallRecord,
    AttemptRecordRequest,
    AttemptRecordResponse,
    MasteryResponse,
    WeakConceptsResponse,
    RecommendResponse,
    QuizGenerateRequest,
    QuizGenerateResponse,
    FlashcardsGenerateRequest,
    FlashcardsGenerateResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
    CheckAnswerRequest,
    CheckAnswerResponse,
)
from backend.agent.teacher import teacher_agent, get_mock_binary_search_steps, get_mock_recursion_steps
from backend.agent.tools import execute_tool_call
from backend.agent.llm_router import router
from backend.agent.client import learner_client, assess_client

logger = logging.getLogger("agent_service")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-seed SQLite DB at startup if running on ephemeral disk (Render)
    try:
        from backend.learner.service import learner_service
        from backend.learner.seed import seed_demo_data
        conn = learner_service._get_conn()
        cur = conn.execute("SELECT COUNT(*) FROM attempts WHERE user_id = 'demo_student'")
        if cur.fetchone()[0] == 0:
            seed_demo_data(conn)
            print("[Lifespan] SQLite database automatically seeded for demo_student on startup.")
    except Exception as e:
        print(f"[Lifespan] SQLite auto-seed check skipped: {e}")
    yield


app = FastAPI(
    title="AI Virtual Teacher Agent Brain & Service Contracts",
    description="Backend agent powering interactive lesson planning, tool calling, whiteboard commands, and contracts for Learner Model and Assessment engines.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for local Next.js and static frontends (Classroom 3000, Dashboard 3001, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8000",
        "http://localhost:8002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8002",
        "*",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health_check():
    """Returns agent service health, LLM routing mode, active keys, reachability, and teammate service modes."""
    return {
        "status": "healthy",
        "service": "backend/agent",
        "mock_mode": router.mock_mode,
        "services": {
            "learner": {
                "mode": learner_client.get_mode(),
                "base_url": learner_client.base_url,
                "in_process_available": learner_client.has_in_process(),
            },
            "assess": {
                "mode": assess_client.get_mode(),
                "base_url": assess_client.base_url,
                "in_process_available": assess_client.has_in_process(),
            }
        },
        "providers": router.get_provider_status()
    }


@app.get("/debug/llm-ping", tags=["Diagnostics"])
async def debug_llm_ping():
    """Runs a tiny live test call against each configured LLM provider and returns latency and reachability."""
    return router.ping_all()


@app.get("/debug/llm-stats", tags=["Diagnostics"])
async def debug_llm_stats():
    """Returns aggregated operational metrics for LLM calls (calls by source, provider, latency, errors)."""
    return router.get_stats()



# =====================================================================
# TEACHER AGENT ENDPOINTS (/backend/agent)
# =====================================================================

@app.post("/lesson/step", response_model=LessonStep, tags=["Lesson"])
async def get_lesson_step(req: LessonStepRequest):
    """
    Generate or retrieve the next teaching step.
    Includes whiteboard draw commands, narration, optional code action, and checkpoint question.
    """
    try:
        step = await teacher_agent.get_next_step(req)
        return step
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate step: {str(e)}")


@app.post("/lesson/check-answer", response_model=CheckAnswerResponse, tags=["Lesson"])
async def check_answer(req: CheckAnswerRequest):
    """
    Directly evaluate a checkpoint question answer.
    Diagnoses misconceptions, returns targeted remediation, updates learner mastery,
    and returns corrective whiteboard commands.
    """
    return teacher_agent.evaluate_check_answer(req)


async def stream_lesson_generator(concept: str, student_id: str) -> AsyncGenerator[str, None]:
    """Yields Server-Sent Events (SSE) for each step in sequence."""
    steps = get_mock_binary_search_steps()
    for step in steps:
        payload = step.model_dump_json()
        yield f"event: step\ndata: {payload}\n\n"
        await asyncio.sleep(0.5)
    yield "event: complete\ndata: {\"status\": \"lesson_finished\"}\n\n"


@app.get("/lesson/step/stream", tags=["Lesson"])
async def stream_lesson(
    concept: str = Query(default="Binary Search", description="Concept topic"),
    student_id: str = Query(default="demo_student", description="Student ID")
):
    """
    Stream teaching steps sequentially via Server-Sent Events (SSE).
    Teammates on frontend can listen with EventSource or fetch reader.
    """
    return StreamingResponse(
        stream_lesson_generator(concept, student_id),
        media_type="text/event-stream"
    )


@app.get("/mock/lesson", response_model=List[LessonStep], tags=["Mock"])
async def get_mock_lesson(
    concept: str = Query(default="Binary Search", description="Lesson topic ('Binary Search' or 'Recursion')")
):
    """
    Returns the complete pre-baked 5-step lesson for Binary Search or Recursion.
    Teammates can use this to build and test their UI/assessments offline.
    """
    if "recursion" in concept.lower():
        return get_mock_recursion_steps()
    return get_mock_binary_search_steps()


@app.post("/demo/seed", tags=["Demo"])
async def seed_demo():
    """
    Seed initial benchmark student persona (Alex Chen) and demo topics.
    Reuses Person 4's existing learner seed engine.
    """
    try:
        from backend.learner.seed import seed_demo_data
        seed_demo_data()
        return {
            "status": "seeded",
            "student_id": "demo_student",
            "name": "Alex Chen",
            "topics": ["Binary Search", "Recursion"]
        }
    except Exception as e:
        return {"status": "seeded_fallback", "detail": str(e)}


@app.post("/demo/reset", tags=["Demo"])
async def reset_demo():
    """
    Reset demo student state back to clean benchmark scenario.
    Reuses Person 4's existing learner seed engine.
    """
    try:
        from backend.learner.seed import seed_demo_data
        seed_demo_data()
        return {
            "status": "reset",
            "student_id": "demo_student",
            "message": "Demo student data reset to benchmark baseline."
        }
    except Exception as e:
        return {"status": "reset_fallback", "detail": str(e)}


@app.post("/agent/chat", response_model=ChatMessageResponse, tags=["Interaction"])
async def chat_with_teacher(req: ChatMessageRequest):
    """Student sends a question or 'I don't understand'; teacher replies with guidance and board hints."""
    try:
        return await teacher_agent.handle_chat(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.post("/tools/execute", response_model=ToolCallRecord, tags=["Tools"])
async def execute_tool(req: ToolCallRequest):
    """Directly execute an agent tool (draw_on_board, run_code, ask_check_question, etc.)."""
    return execute_tool_call(req.tool_name, req.parameters)


# =====================================================================
# LEARNER API CONTRACT ENDPOINTS (Owned by Person 4: /backend/learner)
# =====================================================================

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
    return learner_client.record_attempt(req)


@app.get(
    "/learner/mastery/{user_id}",
    response_model=MasteryResponse,
    tags=["Learner Model"],
    summary="Get mastery scores for all concepts"
)
async def get_mastery(user_id: str = PathParam(..., description="Student ID", examples=["demo_student"])):
    """Returns overall mastery and per-concept scores (0.0 to 1.0)."""
    return learner_client.get_mastery(user_id)


@app.get(
    "/learner/weak/{user_id}",
    response_model=WeakConceptsResponse,
    tags=["Learner Model"],
    summary="Get weak concepts needing practice"
)
async def get_weak_concepts(user_id: str = PathParam(..., description="Student ID", examples=["demo_student"])):
    """Returns list of weak concepts (mastery < 0.60) and active misconceptions."""
    return learner_client.get_weak_concepts(user_id)


@app.get(
    "/learner/recommend/{user_id}",
    response_model=RecommendResponse,
    tags=["Learner Model"],
    summary="Get next recommended topic or lesson"
)
async def get_recommendation(user_id: str = PathParam(..., description="Student ID", examples=["demo_student"])):
    """Returns the highest priority concept recommendation and suggested action."""
    return learner_client.recommend_next(user_id)


@app.get(
    "/learner/history/{user_id}",
    tags=["Learner Model"],
    summary="Get recent practice attempt history"
)
async def get_history(
    user_id: str = PathParam(..., description="Student ID"),
    limit: int = Query(default=20, ge=1, le=100)
):
    """Returns chronological attempt logs with time spent and misconception tags."""
    return learner_client.get_history(user_id, limit=limit)


@app.get(
    "/learner/summary/{user_id}",
    tags=["Learner Model"],
    summary="Full student profile snapshot for dashboard"
)
async def get_summary(user_id: str = PathParam(..., description="Student ID")):
    """Returns aggregate student analytics snapshot for real-time dashboard rendering."""
    return learner_client.get_summary(user_id)


@app.post(
    "/learner/seed",
    tags=["Learner Model"],
    summary="Reset and reseed demo student database"
)
async def reset_learner_seed():
    """Resets the demo student database to initial pitch demo state."""
    return await reset_demo()



# =====================================================================
# ASSESS API CONTRACT ENDPOINTS (Owned by Person 3: /backend/assess)
# =====================================================================

@app.post(
    "/assess/quiz",
    response_model=QuizGenerateResponse,
    tags=["Assessment"],
    summary="Generate a topic-specific quiz"
)
async def generate_quiz(req: QuizGenerateRequest):
    """Generates an MCQ quiz targeted to specified topic and weak concepts."""
    return assess_client.generate_quiz(req)


@app.post(
    "/assess/flashcards",
    response_model=FlashcardsGenerateResponse,
    tags=["Assessment"],
    summary="Generate flashcards for spaced repetition"
)
async def generate_flashcards(req: FlashcardsGenerateRequest):
    """Generates prompt/answer flashcard pairs for memory reinforcement."""
    return assess_client.generate_flashcards(req)


@app.post(
    "/assess/submit",
    response_model=QuizSubmitResponse,
    tags=["Assessment"],
    summary="Submit quiz responses and evaluate"
)
async def submit_quiz(req: QuizSubmitRequest):
    """Evaluates student quiz submissions, computes score, and generates question feedback."""
    return assess_client.submit_quiz(req)


# Mount ElevenLabs TTS router per Member 2 request
try:
    from backend.tts.router import tts_router
    app.include_router(tts_router)
    logger.info("ElevenLabs TTS router mounted on /tts")
except Exception as e:
    logger.warning(f"Could not mount ElevenLabs TTS router: {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run("backend.agent.main:app", host="0.0.0.0", port=port, reload=True)
