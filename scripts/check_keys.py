"""
Key verification helper for AI Virtual Teacher.
Checks whether any free LLM API keys are configured in .env without ever printing secrets.
Exit code:
  0: At least one LLM key is configured.
  1: No LLM keys found (safe for mock mode).
"""

import sys
import pathlib

KEYS_TO_CHECK = [
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
    "CEREBRAS_API_KEY",
    "OPENROUTER_API_KEY",
]


def inspect_env():
    env_file = pathlib.Path(".env")
    configured = {}
    for k in KEYS_TO_CHECK:
        configured[k] = False

    if env_file.exists():
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k in configured and len(v) > 0:
                    configured[k] = True
        except Exception:
            pass

    return configured


def main():
    configured = inspect_env()
    has_any = any(configured.values())

    if "--status" in sys.argv or "-s" in sys.argv:
        print("LLM Provider Configuration Status:")
        for k, is_set in configured.items():
            status = "CONFIGURED" if is_set else "MISSING / BLANK"
            print(f"  - {k}: [{status}]")

    if "--info" in sys.argv or "-i" in sys.argv:
        print("\nFree LLM API Key Providers:")
        print("  1. Google Gemini API:   https://aistudio.google.com/")
        print("  2. Groq Cloud API:      https://console.groq.com/")
        print("  3. Cerebras Cloud API:  https://cloud.cerebras.ai/")
        print("  4. OpenRouter API:      https://openrouter.ai/")
        print("\n(Add any of these to your .env file to enable live AI responses.)\n")

    sys.exit(0 if has_any else 1)


if __name__ == "__main__":
    main()
