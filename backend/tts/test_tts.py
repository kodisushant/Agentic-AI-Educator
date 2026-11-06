"""
Unit & Integration Tests for ElevenLabs TTS Engine (/backend/tts).
All network calls are strictly mocked. Never calls live ElevenLabs API in tests.
"""

import asyncio
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import httpx

from backend.tts.cleaner import strip_markdown_and_latex
from backend.tts.router import (
    tts_router,
    compute_tts_hash,
    CACHE_DIR,
    MAX_TEXT_LENGTH,
)


class TestTTSCleaner(unittest.TestCase):
    def test_strip_markdown(self):
        text = "# Title\nThis is **bold** and *italic* with a [link](https://example.com) and `inline code`."
        cleaned = strip_markdown_and_latex(text)
        self.assertNotIn("#", cleaned)
        self.assertNotIn("**", cleaned)
        self.assertNotIn("*", cleaned)
        self.assertNotIn("`", cleaned)
        self.assertIn("bold and italic with a link and inline code", cleaned)

    def test_strip_code_blocks(self):
        text = "Here is the code:\n```python\ndef solve():\n    return 42\n```\nAnd that is all."
        cleaned = strip_markdown_and_latex(text)
        self.assertNotIn("def solve", cleaned)
        self.assertIn("Here is the code: And that is all.", cleaned)

    def test_strip_latex_display(self):
        text = "Notice the equation: $$\\mathcal{O}(n \\log n)$$ is efficient."
        cleaned = strip_markdown_and_latex(text)
        self.assertNotIn("$$", cleaned)
        self.assertNotIn("\\mathcal", cleaned)

    def test_strip_inline_latex(self):
        text = "The time complexity is $O(\\log_2 n)$ which is fast."
        cleaned = strip_markdown_and_latex(text)
        self.assertNotIn("$", cleaned)
        self.assertIn("log base 2", cleaned)


class TestTTSRouter(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(tts_router)
        self.client = TestClient(self.app)
        self.test_dir = tempfile.mkdtemp()
        self.patcher = patch("backend.tts.router.CACHE_DIR", Path(self.test_dir))
        self.mock_cache_dir = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_status_endpoint_no_secrets(self):
        """Verify GET /tts/status returns operational status without secrets."""
        resp = self.client.get("/tts/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["service"], "backend/tts")
        self.assertIn("key_configured", data)
        self.assertIn("cached_files_count", data)
        self.assertIn("default_voice_configured", data)
        self.assertIn("model", data)
        self.assertIn("max_text_length", data)
        # Ensure no key string is returned
        for val in data.values():
            self.assertNotEqual(str(val), os.getenv("ELEVENLABS_API_KEY", "NON_EXISTENT_KEY"))

    def test_reject_text_over_limit(self):
        """Verify rejection of text over ~600 chars."""
        long_text = "This is a repeated sentence for testing length. " * 20
        self.assertGreater(len(long_text), MAX_TEXT_LENGTH)
        resp = self.client.post("/tts", json={"text": long_text})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("exceeds maximum allowed limit", resp.json()["detail"])

    def test_fallback_when_no_api_key(self):
        """Verify HTTP 503 fallback when ELEVENLABS_API_KEY is missing."""
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": ""}, clear=False):
            resp = self.client.post("/tts", json={"text": "Hello world!"})
            self.assertEqual(resp.status_code, 503)
            self.assertEqual(resp.json(), {"fallback": "browser"})

    def test_cache_hit_returns_without_api_call(self):
        """Verify that cached audio is served directly with zero API calls."""
        text = "Cached audio test sentence."
        cleaned = strip_markdown_and_latex(text)
        voice_id = "test_voice"
        model = "eleven_flash_v2_5"
        h = compute_tts_hash(cleaned, voice_id, model)
        cached_file = self.mock_cache_dir / f"{h}.mp3"
        cached_file.write_bytes(b"MOCK_MP3_DATA_PRE_CACHED")

        with patch("backend.tts.router.synthesize_speech") as mock_synth:
            resp = self.client.post("/tts", json={"text": text, "voice_id": voice_id})
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.content, b"MOCK_MP3_DATA_PRE_CACHED")
            self.assertEqual(resp.headers.get("X-TTS-Cache"), "HIT")
            mock_synth.assert_not_called()

    @patch("backend.tts.router.synthesize_speech", new_callable=AsyncMock)
    def test_cache_miss_calls_api_and_caches(self, mock_synth):
        """Verify cache miss calls ElevenLabs, writes to disk cache, and returns audio."""
        mock_synth.return_value = b"SYNTHESIZED_MP3_PAYLOAD"
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "fake_test_key_123"}, clear=False):
            text = "Synthesize this fresh narration."
            resp = self.client.post("/tts", json={"text": text, "voice_id": "voice_1"})
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.content, b"SYNTHESIZED_MP3_PAYLOAD")
            self.assertEqual(resp.headers.get("X-TTS-Cache"), "MISS")
            mock_synth.assert_called_once()

            # Confirm file was cached
            cleaned = strip_markdown_and_latex(text)
            h = compute_tts_hash(cleaned, "voice_1", "eleven_flash_v2_5")
            cached_file = self.mock_cache_dir / f"{h}.mp3"
            self.assertTrue(cached_file.exists())
            self.assertEqual(cached_file.read_bytes(), b"SYNTHESIZED_MP3_PAYLOAD")

    @patch("backend.tts.router.synthesize_speech", new_callable=AsyncMock)
    def test_api_failure_returns_503_fallback(self, mock_synth):
        """Verify that any API exception (429, timeout, network error) yields HTTP 503 browser fallback."""
        mock_synth.side_effect = RuntimeError("ElevenLabs rate limit 429 quota exceeded")
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "fake_test_key_123"}, clear=False):
            resp = self.client.post("/tts", json={"text": "Fail gracefully please."})
            self.assertEqual(resp.status_code, 503)
            self.assertEqual(resp.json(), {"fallback": "browser"})


if __name__ == "__main__":
    unittest.main()
