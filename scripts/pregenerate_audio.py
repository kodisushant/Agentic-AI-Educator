"""
Pre-generate audio cache for demo lessons via ElevenLabs TTS.
Reads cached demo lessons, computes total character count first,
prompts the user to confirm, and synthesizes each narration sentence into cache/tts/.
"""

import asyncio
import os
import re
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.tts.cleaner import strip_markdown_and_latex
from backend.tts.router import (
    CACHE_DIR,
    compute_tts_hash,
    get_tts_config,
    synthesize_speech,
)


def load_demo_lessons():
    """Extract all demo lesson narrations from teacher definitions and disk cache."""
    narrations = []

    # 1. Load from teacher mock steps (in-process)
    try:
        from backend.agent.teacher import (
            get_mock_binary_search_steps,
            get_mock_recursion_steps,
        )
        bs_steps = get_mock_binary_search_steps()
        rec_steps = get_mock_recursion_steps()
        for s in bs_steps:
            if getattr(s, "narration", None):
                narrations.append(("Binary Search", s.step_index, s.narration))
        for s in rec_steps:
            if getattr(s, "narration", None):
                narrations.append(("Recursion", s.step_index, s.narration))
    except Exception as e:
        print(f"[WARN] Could not load lessons from backend.agent.teacher: {e}")

    # 2. Also inspect backend/agent/.cache for any cached lesson JSON files
    cache_json_dir = PROJECT_ROOT / "backend" / "agent" / ".cache"
    if cache_json_dir.exists():
        import json
        for f in cache_json_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "narration" in data and data["narration"]:
                    topic = data.get("concept", "Demo")
                    idx = data.get("step_index", 0)
                    narrations.append((topic, idx, data["narration"]))
            except Exception:
                pass

    return narrations


def split_into_sentences(text: str):
    """Split a paragraph into distinct narration sentences."""
    cleaned = strip_markdown_and_latex(text)
    # Split on sentence terminals followed by space or end
    raw_sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    valid = []
    for s in raw_sentences:
        s = s.strip()
        if len(s) > 3:  # Skip trivial fragments
            valid.append(s)
    return valid


async def main():
    print("=" * 70)
    print(" ElevenLabs Audio Pre-Generator for Demo Lessons")
    print("=" * 70)

    api_key, voice_id, model = get_tts_config()
    print(f" Voice ID: {voice_id}")
    print(f" Model:    {model}")
    print(f" Cache:    {CACHE_DIR.resolve()}")
    print(f" API Key:  {'[CONFIGURED]' if api_key else '[NOT CONFIGURED]'}\n")

    demo_lessons = load_demo_lessons()
    print(f"[1] Loaded {len(demo_lessons)} lesson step narrations.")

    # Deduplicate sentences
    seen_sentences = set()
    sentence_records = []

    for topic, step_idx, text in demo_lessons:
        sentences = split_into_sentences(text)
        for sentence in sentences:
            if sentence not in seen_sentences:
                seen_sentences.add(sentence)
                h = compute_tts_hash(sentence, voice_id, model)
                cached = (CACHE_DIR / f"{h}.mp3").exists()
                sentence_records.append({
                    "topic": topic,
                    "step": step_idx,
                    "text": sentence,
                    "hash": h,
                    "cached": cached,
                    "chars": len(sentence),
                })

    total_sentences = len(sentence_records)
    cached_sentences = [s for s in sentence_records if s["cached"]]
    pending_sentences = [s for s in sentence_records if not s["cached"]]
    pending_chars = sum(s["chars"] for s in pending_sentences)
    cached_chars = sum(s["chars"] for s in cached_sentences)

    print(f"[2] Sentence Analysis:")
    print(f"    - Total unique sentences: {total_sentences}")
    print(f"    - Already in local cache: {len(cached_sentences)} ({cached_chars} chars)")
    print(f"    - Need synthesis:        {len(pending_sentences)} sentences")
    print(f"    - Total characters:       {pending_chars} chars")

    if not pending_sentences:
        print("\nAll demo narration sentences are already pre-cached! No synthesis required.")
        return

    # Check for non-interactive flag or prompt user
    print("\n----------------------------------------------------------------------")
    print(f" ESTIMATED ELEVENLABS CHARACTERS TO CONSUME: {pending_chars}")
    print(" Free tier quota is approximately 10,000 characters (~10 minutes).")
    print("----------------------------------------------------------------------")

    if not api_key:
        print("[ERROR] Cannot synthesize: ELEVENLABS_API_KEY is not configured in .env.")
        print("Please configure your key before proceeding.")
        return

    # Check CLI args for --yes
    auto_confirm = "--yes" in sys.argv or "-y" in sys.argv
    if not auto_confirm:
        try:
            choice = input(f"Do you want to synthesize {len(pending_sentences)} sentences ({pending_chars} chars)? [y/N]: ").strip().lower()
            if choice not in ("y", "yes"):
                print("[ABORTED] Pre-generation cancelled by user. Zero API calls made.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\n[ABORTED] No user input. Zero API calls made.")
            return

    print("\n[3] Synthesizing and caching audio files...")
    successful = 0
    failed = 0

    for idx, item in enumerate(pending_sentences, 1):
        txt = item["text"]
        h = item["hash"]
        dest = CACHE_DIR / f"{h}.mp3"
        print(f"    [{idx}/{len(pending_sentences)}] ({item['chars']} chars) {txt[:60]}... ", end="", flush=True)

        try:
            audio_bytes = await synthesize_speech(txt, voice_id, model, api_key)
            dest.write_bytes(audio_bytes)
            print("OK [CACHED]")
            successful += 1
        except Exception as e:
            print(f"FAILED ({e})")
            failed += 1

    print("\n" + "=" * 70)
    print(f" Pre-generation complete: {successful} synthesized, {failed} failed, {len(cached_sentences)} already cached.")
    print(f" Cache directory: {CACHE_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
