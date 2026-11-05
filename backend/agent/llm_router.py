import asyncio
import hashlib
import json
import logging
import os
import re
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError

logger = logging.getLogger("llm_router")
T = TypeVar("T", bound=BaseModel)

CACHE_DIR = Path(__file__).resolve().parent / ".cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class LLMRouter:
    def __init__(self):
        self.mock_mode = os.getenv("MOCK_MODE", "true").lower() in ("true", "1", "yes")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.groq_key = os.getenv("GROQ_API_KEY", "").strip()
        self.cerebras_key = os.getenv("CEREBRAS_API_KEY", "").strip()
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()

    def _get_cache_key(self, prompt: str, schema_name: str) -> Path:
        raw = f"{prompt}|{schema_name}"
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return CACHE_DIR / f"{digest}.json"

    def _read_cache(self, cache_file: Path) -> Optional[str]:
        if cache_file.exists():
            try:
                return cache_file.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning(f"Failed to read cache {cache_file}: {e}")
        return None

    def _write_cache(self, cache_file: Path, content: str) -> None:
        try:
            cache_file.write_text(content, encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to write cache {cache_file}: {e}")

    def _extract_json(self, text: str) -> str:
        """Strip markdown fences if present."""
        text = text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            return match.group(1).strip()
        return text

    def _http_post(self, url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout: float = 12.0) -> Dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body)

    async def _call_gemini(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.gemini_key:
            raise ValueError("GEMINI_API_KEY not configured")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        headers = {"Content-Type": "application/json"}
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTIONS:\n{system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
        }
        res = await asyncio.to_thread(self._http_post, url, headers, payload, 15.0)
        return res["candidates"][0]["content"]["parts"][0]["text"]

    async def _call_groq(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.groq_key:
            raise ValueError("GROQ_API_KEY not configured")
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.groq_key}"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }
        res = await asyncio.to_thread(self._http_post, url, headers, payload, 12.0)
        return res["choices"][0]["message"]["content"]

    async def _call_cerebras(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.cerebras_key:
            raise ValueError("CEREBRAS_API_KEY not configured")
        url = "https://api.cerebras.ai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.cerebras_key}"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "llama3.1-8b",
            "messages": messages,
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }
        res = await asyncio.to_thread(self._http_post, url, headers, payload, 15.0)
        return res["choices"][0]["message"]["content"]

    async def _call_openrouter(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.openrouter_key:
            raise ValueError("OPENROUTER_API_KEY not configured")
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openrouter_key}"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "meta-llama/llama-3.2-3b-instruct:free",
            "messages": messages,
            "temperature": 0.2
        }
        res = await asyncio.to_thread(self._http_post, url, headers, payload, 15.0)
        return res["choices"][0]["message"]["content"]

    async def _dispatch_providers(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        providers = [
            ("gemini", self._call_gemini),
            ("groq", self._call_groq),
            ("cerebras", self._call_cerebras),
            ("openrouter", self._call_openrouter),
        ]

        last_error = None
        for name, caller in providers:
            try:
                logger.info(f"Trying LLM provider: {name}")
                result = await caller(prompt, system_prompt)
                logger.info(f"Provider {name} succeeded")
                return result
            except Exception as e:
                logger.warning(f"Provider {name} failed: {e}")
                last_error = e

        raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        mock_fallback_factory: Optional[callable] = None,
    ) -> T:
        schema_name = response_model.__name__
        cache_file = self._get_cache_key(prompt, schema_name)

        # 1. Check disk cache
        cached_content = self._read_cache(cache_file)
        if cached_content:
            try:
                validated = response_model.model_validate_json(cached_content)
                logger.info(f"LLM cache hit for {schema_name}")
                return validated
            except ValidationError:
                pass

        # 2. Check if Mock Mode or no keys configured
        has_any_key = any([self.gemini_key, self.groq_key, self.cerebras_key, self.openrouter_key])
        if self.mock_mode or not has_any_key:
            logger.info("Using mock fallback (MOCK_MODE=true or no keys provided)")
            if mock_fallback_factory:
                result = mock_fallback_factory()
                self._write_cache(cache_file, result.model_dump_json())
                return result
            raise RuntimeError(f"MOCK_MODE active but no fallback factory provided for {schema_name}")

        # 3. Format prompt with schema JSON schema
        json_schema_str = json.dumps(response_model.model_json_schema(), indent=2)
        augmented_prompt = (
            f"{prompt}\n\n"
            f"You MUST return valid JSON adhering strictly to this schema:\n"
            f"```json\n{json_schema_str}\n```\n"
            f"Return ONLY the JSON object, without extra chatter."
        )

        # 4. Attempt call with 1 retry on validation failure
        for attempt in range(2):
            try:
                raw_text = await self._dispatch_providers(augmented_prompt, system_prompt)
                clean_json = self._extract_json(raw_text)
                validated = response_model.model_validate_json(clean_json)
                self._write_cache(cache_file, validated.model_dump_json())
                return validated
            except (ValidationError, Exception) as err:
                logger.warning(f"Validation attempt {attempt + 1} failed: {err}")
                if attempt == 0:
                    augmented_prompt = (
                        f"{prompt}\n\n"
                        f"IMPORTANT: Your previous output failed schema validation with error: {err}.\n"
                        f"Please fix and adhere strictly to this JSON schema:\n"
                        f"```json\n{json_schema_str}\n```\n"
                        f"Return ONLY valid JSON."
                    )
                else:
                    if mock_fallback_factory:
                        logger.warning("Falling back to mock response after retries exhausted")
                        result = mock_fallback_factory()
                        return result
                    raise

        raise RuntimeError("Unreachable state in generate_structured")


# Singleton instance
router = LLMRouter()
