import asyncio
import json
import os
from typing import AsyncGenerator, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.agent.schemas import (
    LessonStep,
    LessonStepRequest,
    ChatMessageRequest,
    ChatMessageResponse,
    ToolCallRequest,
    ToolCallRecord,
)
from backend.agent.teacher import teacher_agent, get_mock_binary_search_steps
from backend.agent.tools import execute_tool_call
from backend.agent.llm_router import router

app = FastAPI(
    title="AI Virtual Teacher Agent Brain",
    description="Backend agent powering interactive lesson planning, tool calling, whiteboard commands, and live coding orchestration.",
    version="1.0.0",
)

# Enable CORS for local Next.js frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health_check():
    """Returns agent service health, LLM routing mode, and active keys status."""
    return {
        "status": "healthy",
        "service": "backend/agent",
        "mock_mode": router.mock_mode,
        "configured_providers": {
            "gemini": bool(router.gemini_key),
            "groq": bool(router.groq_key),
            "cerebras": bool(router.cerebras_key),
            "openrouter": bool(router.openrouter_key),
        }
    }


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
async def get_mock_lesson():
    """
    Returns the complete pre-baked 5-step Binary Search lesson.
    Teammates can use this to build and test their UI/assessments offline.
    """
    return get_mock_binary_search_steps()


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


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run("backend.agent.main:app", host="0.0.0.0", port=port, reload=True)
