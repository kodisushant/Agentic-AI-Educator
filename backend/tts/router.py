"""
FastAPI Router for ElevenLabs Text-to-Speech (TTS) Service.
Provides cached audio synthesis with fallback to browser Web Speech API.
"""

import asyncio
import hashlib
import logging
import os
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.tts.cleaner import strip_markdown_and_latex

logger = logging.getLogger("tts_service")

tts_router = APIRouter(tags=["Text-to-Speech"])

# Locate project cache directory: cache/tts/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = PROJECT_ROOT / "cache" / "tts"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Free plan limit: max 2 concurrent requests
tts_semaphore = asyncio.Semaphore(2)

DEFAULT_MODEL = "eleven_flash_v2_5"
MAX_TEXT_LENGTH = 600


class TTSRequest(BaseModel):
    text: str = Field(..., description="Narration or speech text to synthesize")
    voice_id: Optional[str] = Field(default=None, description="Optional ElevenLabs voice ID")


def get_tts_config():
    """Retrieve TTS environment configuration without leaking secrets."""
    api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM").strip()
    model = os.getenv("TTS_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    return api_key, voice_id, model


def compute_tts_hash(text: str, voice_id: str, model: str) -> str:
    """Compute deterministic SHA-256 cache key for given text, voice, and model."""
    raw = f"{text}|{voice_id}|{model}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def synthesize_speech(cleaned_text: str, voice_id: str, model: str, api_key: str) -> bytes:
    """
    Call ElevenLabs TTS API to synthesize speech audio.
    Enforces concurrency limit (max 2) and returns raw MP3 bytes.
    Raises Exception on any failure.
    """
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY is not configured")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": cleaned_text,
        "model_id": model,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
        },
    }

    async with tts_semaphore:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"ElevenLabs TTS returned HTTP {resp.status_code}: {resp.text[:200]}"
                )
            return resp.content


@tts_router.post("/tts", summary="Synthesize speech audio via ElevenLabs with local file caching")
async def text_to_speech(req: TTSRequest):
    """
    Synthesize speech audio for given text.
    1. Strips markdown, LaTeX, and code blocks.
    2. Rejects text over ~600 chars.
    3. Checks local disk cache (cache/tts/<hash>.mp3).
    4. On cache miss, calls ElevenLabs API (max 2 concurrent).
    5. On any failure, returns HTTP 503 {"fallback":"browser"}.
    """
    cleaned_text = strip_markdown_and_latex(req.text)
    if not cleaned_text:
        raise HTTPException(status_code=400, detail="Text cannot be empty after stripping markdown")

    if len(cleaned_text) > MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Text length ({len(cleaned_text)} chars) exceeds maximum allowed limit ({MAX_TEXT_LENGTH} chars)"
        )

    api_key, default_voice, model = get_tts_config()
    voice_id = (req.voice_id or "").strip() or default_voice

    cache_hash = compute_tts_hash(cleaned_text, voice_id, model)
    cache_file = CACHE_DIR / f"{cache_hash}.mp3"

    # Cache hit: serve cached audio immediately without API call
    if cache_file.exists():
        try:
            audio_bytes = cache_file.read_bytes()
            if len(audio_bytes) > 0:
                return Response(
                    content=audio_bytes,
                    media_type="audio/mpeg",
                    headers={
                        "X-TTS-Cache": "HIT",
                        "X-TTS-Hash": cache_hash,
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to read cached TTS file ({cache_file}): {e}")

    # Cache miss: verify key configuration
    if not api_key:
        logger.info("ElevenLabs API key not configured; signalling browser fallback")
        return JSONResponse(status_code=503, content={"fallback": "browser"})

    # Call ElevenLabs API with graceful fallback on ANY failure
    try:
        audio_bytes = await synthesize_speech(cleaned_text, voice_id, model, api_key)
        # Save to disk cache
        try:
            cache_file.write_bytes(audio_bytes)
        except Exception as write_err:
            logger.warning(f"Failed to write TTS cache file: {write_err}")

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "X-TTS-Cache": "MISS",
                "X-TTS-Hash": cache_hash,
            }
        )
    except Exception as e:
        logger.warning(f"TTS synthesis failure ({e}); falling back to browser speech synthesis")
        return JSONResponse(status_code=503, content={"fallback": "browser"})


@tts_router.get("/tts/status", summary="Check TTS service and cache status without exposing secrets")
async def tts_status():
    """
    Returns non-secret operational status of the TTS service.
    Reports key configuration, cached files count, and default model.
    """
    api_key, voice_id, model = get_tts_config()
    cached_files = list(CACHE_DIR.glob("*.mp3")) if CACHE_DIR.exists() else []

    return {
        "service": "backend/tts",
        "key_configured": bool(api_key),
        "cached_files_count": len(cached_files),
        "default_voice_configured": bool(voice_id),
        "model": model,
        "max_text_length": MAX_TEXT_LENGTH,
        "cache_dir": "cache/tts",
    }
