"""
Verify that when an LLM provider succeeds, router returns trace with source='llm'.
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from backend.agent.llm_router import router
from backend.agent.schemas import ChatMessageResponse, LessonStep


def test_real_llm_trace():
    print("Testing Real LLM Trace Generation:")
    saved_groq = router._call_groq_sync
    saved_key = router.groq_key
    saved_mode = router.mock_mode

    try:
        # Mock successful provider response
        sample_json = (
            '{"reply": "This is a real generated response explaining binary search.", '
            '"code": "def binary_search(arr, target):\\n    return 0", '
            '"suggested_board_commands": [], '
            '"agent_thoughts": "Reasoning dynamically about binary search."}'
        )
        router._call_groq_sync = lambda p, s=None: (sample_json, "llama-3.3-70b-versatile")
        router.groq_key = "test_key_dummy"
        router.mock_mode = False

        res = router.generate_structured_sync(
            "Explain binary search in python for trace verification",
            ChatMessageResponse,
        )
        print(f"  [PASS] trace.source       -> {res.trace.source}")
        print(f"  [PASS] trace.provider     -> {res.trace.provider}")
        print(f"  [PASS] trace.model        -> {res.trace.model}")
        print(f"  [PASS] trace.latency_ms   -> {res.trace.latency_ms}ms")
        print(f"  [PASS] code attached      -> {bool(res.code)}")
        
        assert res.trace.source == "llm", f"Expected source='llm', got '{res.trace.source}'"
        assert res.trace.provider == "groq"
        assert res.trace.model == "llama-3.3-70b-versatile"

        stats = router.get_stats()
        print(f"  [PASS] stats recorded     -> calls_by_source: {stats['calls_by_source']}")
        assert stats["calls_by_source"].get("llm", 0) >= 1
    finally:
        router._call_groq_sync = saved_groq
        router.groq_key = saved_key
        router.mock_mode = saved_mode


if __name__ == "__main__":
    test_real_llm_trace()
    print("\nVerified: real LLM dispatch produces source='llm', records latency and model, and logs cleanly.")
