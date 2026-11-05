import json
import os
import sys
import time
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from backend.agent.schemas import CheckQuestion
from backend.agent.llm_router import LLMRouter, router, load_env_file

load_env_file()


def run_provider_tests():
    router_inst = LLMRouter()
    # Force mock_mode = False for this real test
    router_inst.mock_mode = False

    schema_str = json.dumps(CheckQuestion.model_json_schema(), indent=2)
    prompt = (
        "Create a single multiple choice check question about Binary Search in Python.\n"
        f"Output MUST be valid JSON adhering strictly to this schema:\n```json\n{schema_str}\n```\n"
        "Return ONLY the JSON object."
    )

    providers = [
        ("Gemini", router_inst._call_gemini_sync, router_inst.gemini_key),
        ("Groq", router_inst._call_groq_sync, router_inst.groq_key),
        ("Cerebras", router_inst._call_cerebras_sync, router_inst.cerebras_key),
        ("OpenRouter", router_inst._call_openrouter_sync, router_inst.openrouter_key),
    ]

    print("\n=======================================================")
    print("           REAL LLM PROVIDER TEST RESULTS              ")
    print("=======================================================\n")
    print("| Provider | Configured | Status | Latency (ms) | Schema Validated | Notes |")
    print("|---|---|---|---|---|---|")

    for name, caller, key in providers:
        if not key:
            print(f"| {name} | No | SKIPPED | - | - | Key not present in .env |")
            continue

        start = time.time()
        try:
            raw = caller(prompt)
            latency = int((time.time() - start) * 1000)
            clean = router_inst._extract_json(raw)
            validated = CheckQuestion.model_validate_json(clean)
            print(f"| {name} | Yes | **SUCCESS** | {latency}ms | **PASS** | Valid CheckQuestion: '{validated.question[:30]}...' |")
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            err_msg = str(e).replace("\n", " ")[:60]
            print(f"| {name} | Yes | **FAILED** | {latency}ms | FAIL | {err_msg} |")

    print("\n-------------------------------------------------------")
    print("Testing Fallback Mechanism (Deliberately Corrupting First Provider)")
    print("-------------------------------------------------------")

    # Deliberately break the first active key (Gemini)
    saved_gemini = router_inst.gemini_key
    router_inst.gemini_key = "INVALID_KEY_TEST_FALLBACK"

    test_start = time.time()
    try:
        raw_fallback, serving_provider, latency_ms = router_inst._dispatch_providers_sync(prompt)
        clean = router_inst._extract_json(raw_fallback)
        validated = CheckQuestion.model_validate_json(clean)
        print(f"✓ Fallback succeeded! Gemini failed and fell through to: **{serving_provider}** in {latency_ms}ms")
        print(f"✓ Schema validated question: '{validated.question}'")
        print(f"✓ Correct index: {validated.correct_index}, Concept tag: {validated.concept_tag}")
    except Exception as e:
        print(f"Fallback test failed: {e}")
    finally:
        router_inst.gemini_key = saved_gemini

    print("\n-------------------------------------------------------")
    print("Testing Full Dynamic Lesson Step Generation with Real LLM")
    print("-------------------------------------------------------")
    from backend.agent.teacher import teacher_agent
    from backend.agent.schemas import LessonStepRequest

    # Set router mock_mode to False
    saved_mode = router.mock_mode
    router.mock_mode = False
    try:
        t0 = time.time()
        step = teacher_agent.get_next_step_sync(LessonStepRequest(
            concept="Binary Search",
            student_id="demo_student",
            step_index=0
        ))
        elapsed = int((time.time() - t0) * 1000)
        print(f"✓ Dynamic Lesson Step 0 generated in {elapsed}ms!")
        print(f"✓ Step ID: {step.step_id}")
        print(f"✓ Narration: '{step.narration[:60]}...'")
        print(f"✓ Board commands count: {len(step.board_commands)}")
        print(f"✓ Provider metadata: {step.provider_metadata}")
    except Exception as e:
        print(f"Dynamic lesson generation test failed: {e}")
    finally:
        router.mock_mode = saved_mode


if __name__ == "__main__":
    run_provider_tests()
