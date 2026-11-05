"""
Standalone runner for Assessment Service (/backend/assess).
Can run on its own port or be mounted directly by the tech lead's main app.
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.assess.router import assess_router

app = FastAPI(
    title="Assessment Engine Service",
    description="Quiz & Flashcards Generation, Evaluation, and Learner Model Integration",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assess_router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "backend/assess"}


if __name__ == "__main__":
    port = int(os.getenv("ASSESS_PORT", 8002))
    uvicorn.run("backend.assess.main:app", host="0.0.0.0", port=port, reload=True)

