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

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = ROOT_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
CALLS_LOG_FILE = LOGS_DIR / "llm_calls.log"


def load_env_file(override: bool = True):
    """Load variables from .env if present."""
    env_file = ROOT_DIR / ".env"
    if env_file.exists():
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k:
                        if override or k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass


load_env_file()


def log_llm_call(
    source: str,
    provider: str,
    model: str,
    status: str,
    latency_ms: int,
    prompt_chars: int = 0,
    error: Optional[str] = None
):
    """
    Append an audit log entry for every LLM or mock operation.
    STRICT SECURITY RULE: Never log API keys, tokens, or authorization headers.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    err_str = f" | error=\"{error}\"" if error else ""
    line = f"[{timestamp}] [{status}] source={source} provider={provider} model={model} latency_ms={latency_ms} chars={prompt_chars}{err_str}\n"
    try:
        with open(CALLS_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        logger.warning(f"Failed to write to {CALLS_LOG_FILE}: {e}")


class RateLimitError(Exception):
    """Raised when provider returns HTTP 429."""
    pass


class LLMRouter:
    def __init__(self):
        self.reload_keys()
        self.timeout_per_provider = float(os.getenv("LLM_TIMEOUT", "10.0"))
        self.step_latency_cap = float(os.getenv("STEP_LATENCY_CAP", "25.0"))

        # In-memory stats tracker
        self.stats = {
            "total_calls": 0,
            "calls_by_source": {},
            "calls_by_provider": {},
            "total_latency_ms": 0,
            "error_count": 0,
            "recent_calls": []
        }

    def reload_keys(self):
        load_env_file(override=True)
        self.mock_mode = os.getenv("MOCK_MODE", "true").lower() in ("true", "1", "yes")
        if not getattr(self, "strict_real", False):
            self.strict_real = os.getenv("STRICT_REAL", "false").lower() in ("true", "1", "yes")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.groq_key = os.getenv("GROQ_API_KEY", "").strip()
        self.cerebras_key = os.getenv("CEREBRAS_API_KEY", "").strip()
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
        self.cerebras_model = os.getenv("CEREBRAS_MODEL", "llama3.1-8b").strip()
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.2-3b-instruct:free").strip()

        self.timeout_per_provider = float(os.getenv("LLM_TIMEOUT", "10.0"))
        self.step_latency_cap = float(os.getenv("STEP_LATENCY_CAP", "25.0"))

        # In-memory stats tracker
        self.stats = {
            "total_calls": 0,
            "calls_by_source": {},
            "calls_by_provider": {},
            "total_latency_ms": 0,
            "error_count": 0,
            "recent_calls": []
        }

    def _record_stat(self, source: str, provider: str, model: str, latency_ms: int, status: str):
        self.stats["total_calls"] += 1
        self.stats["calls_by_source"][source] = self.stats["calls_by_source"].get(source, 0) + 1
        self.stats["calls_by_provider"][provider] = self.stats["calls_by_provider"].get(provider, 0) + 1
        self.stats["total_latency_ms"] += latency_ms
        if status != "ok":
            self.stats["error_count"] += 1

        recent = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": source,
            "provider": provider,
            "model": model,
            "latency_ms": latency_ms,
            "status": status
        }
        self.stats["recent_calls"].insert(0, recent)
        if len(self.stats["recent_calls"]) > 50:
            self.stats["recent_calls"].pop()

    def get_stats(self) -> Dict[str, Any]:
        """Return diagnostic metrics for LLM router calls."""
        total = self.stats["total_calls"]
        avg_lat = round(self.stats["total_latency_ms"] / total, 1) if total > 0 else 0.0
        return {
            "total_calls": total,
            "calls_by_source": self.stats["calls_by_source"],
            "calls_by_provider": self.stats["calls_by_provider"],
            "average_latency_ms": avg_lat,
            "error_count": self.stats["error_count"],
            "mock_mode": self.mock_mode,
            "strict_real": self.strict_real,
            "recent_calls": self.stats["recent_calls"][:15]
        }

    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Report which provider keys exist and their reachability status."""
        return {
            "gemini": {
                "key_configured": bool(self.gemini_key),
                "model": self.gemini_model,
                "reachable": bool(self.gemini_key) and not self.mock_mode,
            },
            "groq": {
                "key_configured": bool(self.groq_key),
                "model": self.groq_model,
                "reachable": bool(self.groq_key) and not self.mock_mode,
            },
            "cerebras": {
                "key_configured": bool(self.cerebras_key),
                "model": self.cerebras_model,
                "reachable": bool(self.cerebras_key) and not self.mock_mode,
            },
            "openrouter": {
                "key_configured": bool(self.openrouter_key),
                "model": self.openrouter_model,
                "reachable": bool(self.openrouter_key) and not self.mock_mode,
            }
        }

    def ping_provider(self, provider_name: str) -> Dict[str, Any]:
        """Make a tiny real call to verify provider reachability and latency without mock fallback."""
        t0 = time.time()
        tiny_prompt = 'Respond strictly with valid JSON: {"status": "ok", "ping": "pong"}'
        callers = {
            "gemini": (self._call_gemini_sync, self.gemini_key, self.gemini_model),
            "groq": (self._call_groq_sync, self.groq_key, self.groq_model),
            "cerebras": (self._call_cerebras_sync, self.cerebras_key, self.cerebras_model),
            "openrouter": (self._call_openrouter_sync, self.openrouter_key, self.openrouter_model),
        }
        if provider_name not in callers:
            return {
                "provider": provider_name,
                "configured": False,
                "success": False,
                "error": "Unknown provider"
            }

        caller, key, model = callers[provider_name]
        if not key:
            return {
                "provider": provider_name,
                "configured": False,
                "success": False,
                "model": model,
                "latency_ms": 0,
                "error": "API key not set in .env"
            }

        try:
            raw_text, used_model = caller(tiny_prompt)
            latency_ms = int((time.time() - t0) * 1000)
            self._record_stat("llm", provider_name, used_model, latency_ms, "ok")
            log_llm_call("llm", provider_name, used_model, "SUCCESS", latency_ms)
            return {
                "provider": provider_name,
                "configured": True,
                "success": True,
                "model": used_model,
                "latency_ms": latency_ms,
                "error": None
            }
        except Exception as e:
            latency_ms = int((time.time() - t0) * 1000)
            self._record_stat("llm", provider_name, model, latency_ms, "error")
            log_llm_call("llm", provider_name, model, "ERROR", latency_ms, error=str(e)[:120])
            return {
                "provider": provider_name,
                "configured": True,
                "success": False,
                "model": model,
                "latency_ms": latency_ms,
                "error": str(e)[:120]
            }

    def ping_all(self) -> Dict[str, Any]:
        providers = ["gemini", "groq", "cerebras", "openrouter"]
        results = {}
        for p in providers:
            results[p] = self.ping_provider(p)
        return {
            "status": "complete",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "providers": results
        }

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
        """Strip markdown fences and extract outermost JSON object."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end + 1]
        return text

    def _http_post(self, url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
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

    def _call_gemini_sync(self, prompt: str, system_prompt: Optional[str] = None) -> Tuple[str, str]:
        if not self.gemini_key:
            raise ValueError("GEMINI_API_KEY not configured")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_key}"
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
        return res["candidates"][0]["content"]["parts"][0]["text"], self.gemini_model

    def _call_groq_sync(self, prompt: str, system_prompt: Optional[str] = None) -> Tuple[str, str]:
        if not self.groq_key:
            raise ValueError("GROQ_API_KEY not configured")
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.groq_key}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Virtual-Teacher/1.0"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Try active Groq models in priority order (fast to capable)
        known_working = [
            "llama-3.1-8b-instant",
            "llama3-8b-8192",
            "llama-3.3-70b-versatile",
            "llama3-70b-8192",
            "gemma2-9b-it",
            "mixtral-8x7b-32768",
        ]
        models_to_try = []
        # Always try configured model first (unless it's one of the broken openai/* ones)
        if self.groq_model and not self.groq_model.startswith("openai/") and not self.groq_model.startswith("qwen/"):
            models_to_try.append(self.groq_model)
        for alt in known_working:
            if alt not in models_to_try:
                models_to_try.append(alt)

        last_err = None
        for model_name in models_to_try:
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }
            try:
                res = self._http_post(url, headers, payload, timeout=self.timeout_per_provider)
                self.groq_model = model_name
                return res["choices"][0]["message"]["content"], model_name
            except RateLimitError as rle:
                last_err = rle
                logger.warning(f"Groq model {model_name} rate limited (429), trying next Groq model: {rle}")
                continue
            except RuntimeError as re:
                if "model_not_found" in str(re) or "404" in str(re) or "decommissioned" in str(re):
                    last_err = re
                    continue
                raise
        if last_err:
            raise last_err
        raise RuntimeError("No Groq model succeeded")

    def _call_cerebras_sync(self, prompt: str, system_prompt: Optional[str] = None) -> Tuple[str, str]:
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
            "model": self.cerebras_model,
            "messages": messages,
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }
        res = self._http_post(url, headers, payload, timeout=self.timeout_per_provider)
        return res["choices"][0]["message"]["content"], self.cerebras_model

    def _call_openrouter_sync(self, prompt: str, system_prompt: Optional[str] = None) -> Tuple[str, str]:
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
            "model": self.openrouter_model,
            "messages": messages,
            "temperature": 0.2
        }
        res = self._http_post(url, headers, payload, timeout=self.timeout_per_provider)
        return res["choices"][0]["message"]["content"], self.openrouter_model

    def _dispatch_providers_sync(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        only_provider: Optional[str] = None
    ) -> Tuple[str, str, str, int]:
        """
        Dispatches request through the provider fallback chain synchronously.
        If only_provider is specified (e.g. 'groq'), dispatches strictly to that provider.
        """
        self.reload_keys()
        if only_provider == "groq":
            providers = [("groq", self._call_groq_sync)]
        else:
            providers = [
                ("groq", self._call_groq_sync),
                ("gemini", self._call_gemini_sync),
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
                raw_text, used_model = caller(prompt, system_prompt)
                latency_ms = int((time.time() - t0) * 1000)
                logger.info(f"Provider {name} succeeded in {latency_ms}ms with model {used_model}")
                return raw_text, name, used_model, latency_ms
            except RateLimitError as rle:
                latency_ms = int((time.time() - t0) * 1000)
                logger.warning(f"Provider {name} rate limited (429) after {latency_ms}ms: {rle}. Falling to next provider.")
                errors.append(f"{name}: 429 RateLimit")
            except Exception as e:
                latency_ms = int((time.time() - t0) * 1000)
                logger.warning(f"Provider {name} failed after {latency_ms}ms: {e}. Falling to next provider.")
                errors.append(f"{name}: {str(e)[:80]}")

        raise RuntimeError(f"All LLM providers failed or timed out: {'; '.join(errors)}")

    async def _dispatch_providers(self, prompt: str, system_prompt: Optional[str] = None, only_provider: Optional[str] = None) -> Tuple[str, str, str, int]:
        return await asyncio.to_thread(self._dispatch_providers_sync, prompt, system_prompt, only_provider)

    def generate_structured_sync(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        mock_fallback_factory: Optional[callable] = None,
        only_provider: Optional[str] = None,
    ) -> T:
        schema_name = response_model.__name__
        cache_file = self._get_cache_key(prompt, schema_name)
        self.reload_keys()

        # 1. Check disk cache
        cached_content = self._read_cache(cache_file)
        if cached_content:
            try:
                validated = response_model.model_validate_json(cached_content)
                logger.info(f"LLM cache hit for {schema_name}")
                self._record_stat("cache", "cache", "disk_cache", 0, "ok")
                log_llm_call("cache", "cache", "disk_cache", "CACHE_HIT", 0, len(prompt))
                if hasattr(validated, "trace"):
                    if validated.trace is None:
                        from backend.agent.schemas import AgentTrace
                        validated.trace = AgentTrace(source="cache", provider="cache", model="disk_cache", latency_ms=0, provider_used="cache")
                    else:
                        validated.trace.source = "cache"
                        validated.trace.provider = "cache"
                        validated.trace.model = "disk_cache"
                        validated.trace.latency_ms = 0
                        validated.trace.provider_used = "cache"
                return validated
            except ValidationError:
                pass

        # 2. Check if Mock Mode or no keys configured
        use_real = (only_provider == "groq" and bool(self.groq_key)) or (
            not self.mock_mode and any([self.gemini_key, self.groq_key, self.cerebras_key, self.openrouter_key])
        )

        if not use_real:
            if self.strict_real:
                err_msg = "STRICT_REAL=true is set, but MOCK_MODE is enabled or no provider API keys are configured."
                self._record_stat("mock", "none", "none", 0, "error")
                log_llm_call("mock", "none", "none", "STRICT_REAL_BLOCKED", 0, error=err_msg)
                raise RuntimeError(err_msg)

            logger.info("Using mock fallback (MOCK_MODE=true or no keys provided)")
            if mock_fallback_factory:
                result = mock_fallback_factory()
                self._record_stat("mock", "mock", "canned", 0, "ok")
                log_llm_call("mock", "mock", "canned", "MOCK_FALLBACK", 0)
                if hasattr(result, "trace"):
                    if result.trace is None:
                        from backend.agent.schemas import AgentTrace
                        result.trace = AgentTrace(source="mock", provider="mock", model="canned", latency_ms=0, provider_used="mock")
                    else:
                        result.trace.source = "mock"
                        result.trace.provider = "mock"
                        result.trace.model = "canned"
                        result.trace.latency_ms = 0
                        result.trace.provider_used = "mock"
                # DO NOT write mock fallbacks to cache
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
        last_error = None
        for attempt in range(2):
            try:
                raw_text, provider_name, model_name, latency_ms = self._dispatch_providers_sync(
                    augmented_prompt, system_prompt, only_provider=only_provider
                )
                clean_json = self._extract_json(raw_text)
                validated = response_model.model_validate_json(clean_json)
                self._record_stat("llm", provider_name, model_name, latency_ms, "ok")
                log_llm_call("llm", provider_name, model_name, "SUCCESS", latency_ms, len(prompt))
                
                if hasattr(validated, "trace"):
                    if validated.trace is None:
                        from backend.agent.schemas import AgentTrace
                        validated.trace = AgentTrace(
                            source="llm",
                            provider=provider_name,
                            model=model_name,
                            latency_ms=latency_ms,
                            provider_used=provider_name
                        )
                    else:
                        validated.trace.source = "llm"
                        validated.trace.provider = provider_name
                        validated.trace.model = model_name
                        validated.trace.latency_ms = latency_ms
                        validated.trace.provider_used = provider_name

                # Cache successful REAL LLM response
                self._write_cache(cache_file, validated.model_dump_json())
                return validated
            except Exception as err:
                last_error = err
                logger.warning(f"LLM generation attempt {attempt + 1} failed: {err}")
                if attempt == 0:
                    augmented_prompt = (
                        f"{prompt}\n\n"
                        f"IMPORTANT: Your previous output failed schema validation with error: {err}.\n"
                        f"Please fix and adhere strictly to this JSON schema:\n"
                        f"```json\n{json_schema_str}\n```\n"
                        f"Return ONLY valid JSON."
                    )
                else:
                    self._record_stat("llm", "failed", "failed", 0, "error")
                    log_llm_call("llm", "failed", "failed", "FAILED", 0, error=str(last_error)[:120])
                    if self.strict_real:
                        raise RuntimeError(f"STRICT_REAL=true is set: LLM generation failed: {last_error}")
                    if mock_fallback_factory:
                        logger.warning("Falling back to mock response after retries exhausted")
                        result = mock_fallback_factory()
                        if hasattr(result, "trace"):
                            if result.trace is None:
                                from backend.agent.schemas import AgentTrace
                                result.trace = AgentTrace(source="fallback_canned", provider="mock_fallback_on_error", model="canned", latency_ms=0, provider_used="mock")
                            else:
                                result.trace.source = "fallback_canned"
                                result.trace.provider = "mock_fallback_on_error"
                                result.trace.model = "canned"
                                result.trace.latency_ms = 0
                                result.trace.provider_used = "mock"
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
