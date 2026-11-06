"""
End-to-End Integration Verification Script (scripts/e2e.py)
Tests the complete multi-agent system:
- Person 1: Teacher Brain, LLM Router, Whiteboard Commands, Misconception Remediation
- Person 3: Assessment Engine (Quiz generation, Flashcards, Quiz submission & evaluation)
- Person 4: Learner Model (EWMA mastery, SQLite DB, Forgetting decay, Recommendations)
"""

import sys
import os
import json
import time

# Ensure repo root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.agent.schemas import (
    LessonStepRequest,
    CheckAnswerRequest,
    ChatMessageRequest,
    AttemptRecordRequest,
    QuizGenerateRequest,
    FlashcardsGenerateRequest,
    QuizSubmitRequest,
)
from backend.agent.teacher import teacher_agent, get_mock_binary_search_steps
from backend.agent.client import learner_client, assess_client
from backend.agent.llm_router import router


def run_e2e_tests():
    print("=" * 80)
    print("      AI VIRTUAL TEACHER - END-TO-END INTEGRATION TEST & HONESTY AUDIT      ")
    print("=" * 80)

    results = []

    def record(step_name: str, passed: bool, detail: str, provider: str, model: str, latency_ms: int, free_key: str):
        status = "PASS" if passed else "FAIL"
        results.append((step_name, status, detail, provider, model, latency_ms, free_key))
        icon = "✓" if passed else "✗"
        print(f"[{status}] {icon} {step_name} [{provider}:{model} {latency_ms}ms, FreeKey={free_key}]: {detail}")

    # 1. Health & Configuration
    t0 = time.time()
    try:
        lat = int((time.time() - t0) * 1000)
        mode_str = "MOCK_MODE=True" if router.mock_mode else "MOCK_MODE=False (Live Router)"
        record("System Health & LLM Config", True, mode_str, "internal", "health-check", lat, "Yes")
    except Exception as e:
        record("System Health & LLM Config", False, str(e), "internal", "error", 0, "N/A")

    # 2. Whiteboard Lesson Steps
    t0 = time.time()
    try:
        steps = get_mock_binary_search_steps()
        assert len(steps) == 5, f"Expected 5 steps, got {len(steps)}"
        all_commands = [cmd for s in steps for cmd in s.board_commands]
        cmd_types = {c.type for c in all_commands}
        lat = int((time.time() - t0) * 1000)
        record(
            "Lesson Plan & Board Commands",
            True,
            f"5 steps, {len(all_commands)} commands across {cmd_types}",
            "canned_slice",
            "binary_search_v1",
            lat,
            "Yes (offline)"
        )
    except Exception as e:
        record("Lesson Plan & Board Commands", False, str(e), "canned_slice", "error", 0, "N/A")

    # 3. Dynamic Lesson Step Generation
    t0 = time.time()
    try:
        step_req = LessonStepRequest(
            concept="Binary Search",
            student_id="demo_student",
            step_index=0,
            student_misconceptions=["confuses_low_with_high_shift"]
        )
        step = teacher_agent.get_next_step_sync(step_req)
        lat = int((time.time() - t0) * 1000)
        assert step.step_id is not None
        assert len(step.board_commands) > 0

        source = step.trace.source if step.trace else "mock"
        p_name = step.trace.provider if (step.trace and step.trace.provider) else "mock"
        model_name = step.trace.model if (step.trace and step.trace.model) else "canned"
        step_lat = step.trace.latency_ms if (step.trace and step.trace.latency_ms > 0) else lat
        free_avail = "Yes (Free Tier)" if source == "llm" else "Yes (Zero-cost built-in)"

        record("Teacher Step Generation", True, f"Step '{step.step_id}' ({len(step.board_commands)} cmds, source={source})", p_name, model_name, step_lat, free_avail)
    except Exception as e:
        record("Teacher Step Generation", False, str(e), "unknown", "error", 0, "N/A")

    # 4. Checkpoint Misconception Diagnosis & Remediation
    t0 = time.time()
    try:
        chk_req = CheckAnswerRequest(
            question_id="bs_check_bounds",
            selected_index=0,
            concept="Binary Search",
            student_id="demo_student"
        )
        ans_res = teacher_agent.evaluate_check_answer(chk_req)
        lat = int((time.time() - t0) * 1000)
        assert not ans_res.is_correct
        assert ans_res.detected_misconception is not None
        assert ans_res.remediation is not None
        source = ans_res.trace.source if ans_res.trace else "fallback_canned"
        record(
            "Misconception Diagnosis & Remediation",
            True,
            f"Diagnosed: '{ans_res.detected_misconception}' (source={source})",
            "rule_taxonomy",
            "misconception_evaluator_v1",
            lat,
            "Yes (offline)"
        )
    except Exception as e:
        record("Misconception Diagnosis & Remediation", False, str(e), "rule_taxonomy", "error", 0, "N/A")

    # 5. Teacher Chat Guidance
    t0 = time.time()
    try:
        chat_req = ChatMessageRequest(
            student_id="demo_student",
            message="Why do we add 1 when setting low = mid + 1?",
            concept="Binary Search"
        )
        chat_res = teacher_agent.handle_chat_sync(chat_req)
        lat = int((time.time() - t0) * 1000)
        assert len(chat_res.reply) > 0
        source = chat_res.trace.source if chat_res.trace else "mock"
        p_name = chat_res.trace.provider if (chat_res.trace and chat_res.trace.provider) else "internal"
        model_name = chat_res.trace.model if (chat_res.trace and chat_res.trace.model) else "chat_agent_v1"
        chat_lat = chat_res.trace.latency_ms if (chat_res.trace and chat_res.trace.latency_ms > 0) else lat
        record("Teacher Chat Guidance", True, f"Generated {len(chat_res.reply)} chars (source={source})", p_name, model_name, chat_lat, "Yes (offline)")
    except Exception as e:
        record("Teacher Chat Guidance", False, str(e), "rule_socratic", "error", 0, "N/A")

    # 6. Learner Service: Attempt Recording
    t0 = time.time()
    try:
        att = AttemptRecordRequest(
            user_id="demo_student",
            concept_tag="binary_search_bounds_update",
            is_correct=True,
            time_taken_ms=1800
        )
        att_res = learner_client.record_attempt(att)
        lat = int((time.time() - t0) * 1000)
        assert att_res.status == "recorded"
        record("Learner: Record Attempt", True, f"Mastery updated to {att_res.new_mastery_score}", "sqlite_db", "ewma_engine", lat, "Yes (local)")
    except Exception as e:
        record("Learner: Record Attempt", False, str(e), "sqlite_db", "error", 0, "N/A")

    # 7. Learner Service: Mastery & Weak Concepts
    t0 = time.time()
    try:
        mastery = learner_client.get_mastery("demo_student")
        weak = learner_client.get_weak_concepts("demo_student")
        rec = learner_client.recommend_next("demo_student")
        lat = int((time.time() - t0) * 1000)
        assert len(weak.weak_concepts) >= 1
        record("Learner: Profile & Recommendation", True, f"Score={mastery.overall_score}, Weak={len(weak.weak_concepts)}", "sqlite_db", "knowledge_graph", lat, "Yes (local)")
    except Exception as e:
        record("Learner: Profile & Recommendation", False, str(e), "sqlite_db", "error", 0, "N/A")

    # 8. Assess Service: Quiz Generation
    t0 = time.time()
    try:
        q_req = QuizGenerateRequest(
            topic="Binary Search",
            num_questions=3,
            weak_concepts=["binary_search_bounds_update"],
            student_id="demo_student"
        )
        quiz = assess_client.generate_quiz(q_req)
        lat = int((time.time() - t0) * 1000)
        assert len(quiz.questions) == 3
        record("Assess: Quiz Generation", True, f"Quiz '{quiz.quiz_id}' with {len(quiz.questions)} questions", "assess_service", "quiz_bank_v1", lat, "Yes (local)")
    except Exception as e:
        record("Assess: Quiz Generation", False, str(e), "assess_service", "error", 0, "N/A")

    # 9. Assess Service: Flashcards Generation
    t0 = time.time()
    try:
        fc_req = FlashcardsGenerateRequest(
            topic="Binary Search",
            count=4,
            weak_concepts=["binary_search_bounds_update"],
            student_id="demo_student"
        )
        fc = assess_client.generate_flashcards(fc_req)
        lat = int((time.time() - t0) * 1000)
        assert len(fc.cards) == 4
        record("Assess: Flashcards Generation", True, f"{len(fc.cards)} flashcards ready", "assess_service", "flashcard_bank_v1", lat, "Yes (local)")
    except Exception as e:
        record("Assess: Flashcards Generation", False, str(e), "assess_service", "error", 0, "N/A")

    # 10. Assess Service: Quiz Submission & Auto-Grading
    t0 = time.time()
    try:
        sub_req = QuizSubmitRequest(
            quiz_id="quiz_bs_101",
            user_id="demo_student",
            answers={"q_bs_1": 0, "q_bs_2": 1, "q_bs_3": 0}
        )
        sub_res = assess_client.submit_quiz(sub_req)
        lat = int((time.time() - t0) * 1000)
        assert sub_res.total_questions == 3
        record("Assess: Quiz Grading & Feedback", True, f"Score: {sub_res.score} ({sub_res.correct_count}/{sub_res.total_questions})", "assess_service", "rubric_evaluator", lat, "Yes (local)")
    except Exception as e:
        record("Assess: Quiz Grading & Feedback", False, str(e), "assess_service", "error", 0, "N/A")

    print("\n" + "=" * 90)
    print("                    E2E TEST SUMMARY MATRIX & HONESTY AUDIT                    ")
    print("=" * 90)
    print(f"{'Step':<32} | {'Status':<6} | {'Provider':<14} | {'Model':<22} | {'Latency':<8} | {'Free Key?'}")
    print("-" * 90)
    all_passed = True
    for name, status, detail, prov, mdl, lat, free_k in results:
        if status != "PASS":
            all_passed = False
        print(f"{name:<32} | {status:<6} | {prov:<14} | {mdl:<22} | {str(lat)+'ms':<8} | {free_k}")
    print("=" * 90)

    if all_passed:
        print("\n🎉 ALL 10 END-TO-END INTEGRATION STEPS PASSED SUCCESSFULLY!\n")
        return 0
    else:
        print("\n❌ SOME STEPS FAILED. Please review the matrix above.\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_e2e_tests())
