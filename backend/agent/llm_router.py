import asyncio
import hashlib
import json
import logging
import os
import re
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar
from pydantic import BaseModel, ValidationError

logger = logging.getLogger("llm_router")
T = TypeVar("T", bound=BaseModel)

CACHE_DIR = Path(__file__).resolve().parent / ".cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def load_env_file():
    """Load variables from .env if present and not already in os.environ."""
    root = Path(__file__).resolve().parent.parent.parent
    env_file = root / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v


load_env_file()


class RateLimitError(Exception):
    """Raised when provider returns HTTP 429."""
    pass


class LLMRouter:
    def __init__(self):
        load_env_file()
        self.mock_mode = os.getenv("MOCK_MODE", "true").lower() in ("true", "1", "yes")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.groq_key = os.getenv("GROQ_API_KEY", "").strip()
        self.cerebras_key = os.getenv("CEREBRAS_API_KEY", "").strip()
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.timeout_per_provider = float(os.getenv("LLM_TIMEOUT", "10.0"))
        self.step_latency_cap = float(os.getenv("STEP_LATENCY_CAP", "25.0"))

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

    def _http_post(self, url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        # Ensure default User-Agent to avoid Cloudflare/WAF block (e.g. error 1010)
        req_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Virtual-Teacher/1.0", **headers}
        req = urllib.request.Request(url, data=data, headers=req_headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                res_body = response.read().decode("utf-8")
                return json.loads(res_body)
        except urllib.error.HTTPError as he:
            body = ""
            try:
                body = he.read().decode("utf-8")
            except Exception:
                pass
            if he.code == 429:
                logger.warning(f"HTTP 429 Rate Limit from {url}: {body}")
                raise RateLimitError(f"Provider rate limit exceeded (429): {body}")
            logger.warning(f"HTTP error {he.code} from {url}: {body}")
            raise RuntimeError(f"HTTP error {he.code}: {body}") from he
        except (TimeoutError, urllib.error.URLError) as te:
            logger.warning(f"Request timeout/connection error to {url}: {te}")
            raise

    # --- Provider synchronous callers ---

    def _call_gemini_sync(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.gemini_key:
            raise ValueError("GEMINI_API_KEY not configured")
        # Use active Google AI Studio model: gemini-3.1-flash-lite
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={self.gemini_key}"
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
        res = self._http_post(url, headers, payload, timeout=self.timeout_per_provider)
        return res["candidates"][0]["content"]["parts"][0]["text"]

    def _call_groq_sync(self, prompt: str, system_prompt: Optional[str] = None) -> str:
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
            "model": "qwen/qwen3.8-27b",
            "messages": messages,
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }
        res = self._http_post(url, headers, payload, timeout=self.timeout_per_provider)
        return res["choices"][0]["message"]["content"]

    def _call_cerebras_sync(self, prompt: str, system_prompt: Optional[str] = None) -> str:
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
        res = self._http_post(url, headers, payload, timeout=self.timeout_per_provider)
        return res["choices"][0]["message"]["content"]

    def _call_openrouter_sync(self, prompt: str, system_prompt: Optional[str] = None) -> str:
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
        res = self._http_post(url, headers, payload, timeout=self.timeout_per_provider)
        return res["choices"][0]["message"]["content"]

    def _dispatch_providers_sync(self, prompt: str, system_prompt: Optional[str] = None) -> Tuple[str, str, int]:
        """
        Dispatches request through the provider fallback chain synchronously.
        Fallback order: Gemini -> Groq -> Cerebras -> OpenRouter.
        Returns: (raw_response_text, provider_name, latency_ms)
        """
        providers = [
            ("gemini", self._call_gemini_sync),
            ("groq", self._call_groq_sync),
            ("cerebras", self._call_cerebras_sync),
            ("openrouter", self._call_openrouter_sync),
        ]

        errors = []
        start_overall = time.time()

        for name, caller in providers:
            # Check step latency cap
            elapsed_total = time.time() - start_overall
            if elapsed_total > self.step_latency_cap:
                logger.warning(f"Step latency cap ({self.step_latency_cap}s) reached after {elapsed_total:.2f}s")
                break

            t0 = time.time()
            try:
                logger.info(f"Trying LLM provider: {name}")
                result = caller(prompt, system_prompt)
                latency_ms = int((time.time() - t0) * 1000)
                logger.info(f"Provider {name} succeeded in {latency_ms}ms")
                return result, name, latency_ms
            except RateLimitError as rle:
                latency_ms = int((time.time() - t0) * 1000)
                logger.warning(f"Provider {name} rate limited (429) after {latency_ms}ms: {rle}. Falling to next provider.")
                errors.append(f"{name}: 429 RateLimit")
            except Exception as e:
                latency_ms = int((time.time() - t0) * 1000)
                logger.warning(f"Provider {name} failed after {latency_ms}ms: {e}. Falling to next provider.")
                errors.append(f"{name}: {str(e)[:80]}")

        raise RuntimeError(f"All LLM providers failed or timed out: {'; '.join(errors)}")

    async def _dispatch_providers(self, prompt: str, system_prompt: Optional[str] = None) -> Tuple[str, str, int]:
        return await asyncio.to_thread(self._dispatch_providers_sync, prompt, system_prompt)

    def generate_structured_sync(
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
                if hasattr(validated, "provider_metadata") and validated.provider_metadata is None:
                    validated.provider_metadata = {"provider": "cache", "latency_ms": 0, "cached": True}
                return validated
            except ValidationError:
                pass

        # 2. Check if Mock Mode or no keys configured
        has_any_key = any([self.gemini_key, self.groq_key, self.cerebras_key, self.openrouter_key])
        if self.mock_mode or not has_any_key:
            logger.info("Using mock fallback (MOCK_MODE=true or no keys provided)")
            if mock_fallback_factory:
                result = mock_fallback_factory()
                if hasattr(result, "provider_metadata") and result.provider_metadata is None:
                    result.provider_metadata = {"provider": "mock", "latency_ms": 0, "cached": False}
                self._write_cache(cache_file, result.model_dump_json())
                return result
            raise RuntimeError(f"MOCK_MODE active but no fallback factory provided for {schema_name}")

        # 3. Format prompt with JSON schema
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
                raw_text, provider_name, latency_ms = self._dispatch_providers_sync(augmented_prompt, system_prompt)
                clean_json = self._extract_json(raw_text)
                validated = response_model.model_validate_json(clean_json)
                if hasattr(validated, "provider_metadata"):
                    validated.provider_metadata = {
                        "provider": provider_name,
                        "latency_ms": latency_ms,
                        "cached": False,
                    }
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
                        if hasattr(result, "provider_metadata"):
                            result.provider_metadata = {"provider": "mock_fallback_on_error", "latency_ms": 0, "cached": False}
                        return result
                    raise

        raise RuntimeError("Unreachable state in generate_structured_sync")

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        mock_fallback_factory: Optional[callable] = None,
    ) -> T:
        return await asyncio.to_thread(
            self.generate_structured_sync,
            prompt,
            response_model,
            system_prompt,
            mock_fallback_factory
        )


# Singleton instance
router = LLMRouter()
