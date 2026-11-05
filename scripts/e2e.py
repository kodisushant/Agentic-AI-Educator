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
from backend.agent.main import app


def run_e2e_tests():
    print("=" * 65)
    print("      AI VIRTUAL TEACHER - END-TO-END INTEGRATION TEST SUITE      ")
    print("=" * 65)

    results = []

    def record(step_name: str, passed: bool, detail: str = ""):
        status = "PASS" if passed else "FAIL"
        results.append((step_name, status, detail))
        icon = "✓" if passed else "✗"
        print(f"[{status}] {icon} {step_name}: {detail}")

    # 1. Health & Configuration
    try:
        from backend.agent.llm_router import router
        record("System Health & LLM Config", True, f"Mock mode={router.mock_mode}")
    except Exception as e:
        record("System Health & LLM Config", False, str(e))

    # 2. Whiteboard Lesson Steps
    try:
        steps = get_mock_binary_search_steps()
        assert len(steps) == 5, f"Expected 5 steps, got {len(steps)}"
        all_commands = [cmd for s in steps for cmd in s.board_commands]
        cmd_types = {c.type for c in all_commands}
        record("Lesson Plan & Board Commands", True, f"5 steps loaded, {len(all_commands)} commands across types: {cmd_types}")
    except Exception as e:
        record("Lesson Plan & Board Commands", False, str(e))

    # 3. Dynamic Lesson Step Generation
    try:
        step_req = LessonStepRequest(
            concept="Binary Search",
            student_id="demo_student",
            step_index=0,
            student_misconceptions=["confuses_low_with_high_shift"]
        )
        step = teacher_agent.get_next_step_sync(step_req)
        assert step.step_id is not None
        assert len(step.board_commands) > 0
        record("Teacher Step Generation", True, f"Step '{step.step_id}' generated with {len(step.board_commands)} commands")
    except Exception as e:
        record("Teacher Step Generation", False, str(e))

    # 4. Checkpoint Misconception Diagnosis & Remediation
    try:
        chk_req = CheckAnswerRequest(
            question_id="bs_check_bounds",
            selected_index=0,  # "high = mid - 1" (wrong direction when target > mid)
            concept="Binary Search",
            student_id="demo_student"
        )
        ans_res = teacher_agent.evaluate_check_answer(chk_req)
        assert not ans_res.is_correct
        assert ans_res.detected_misconception is not None
        assert ans_res.remediation is not None
        record(
            "Misconception Diagnosis & Remediation",
            True,
            f"Diagnosed: '{ans_res.detected_misconception}' with targeted visual remediation"
        )
    except Exception as e:
        record("Misconception Diagnosis & Remediation", False, str(e))

    # 5. Teacher Chat Interaction
    try:
        chat_req = ChatMessageRequest(
            student_id="demo_student",
            message="Why do we add 1 when setting low = mid + 1?",
            context="Binary Search Bounds Update"
        )
        chat_res = teacher_agent.handle_chat_sync(chat_req)
        assert len(chat_res.reply) > 0
        record("Teacher Chat Guidance", True, f"Reply generated ({len(chat_res.reply)} chars)")
    except Exception as e:
        record("Teacher Chat Guidance", False, str(e))

    # 6. Learner Service: Attempt Recording
    try:
        att = AttemptRecordRequest(
            user_id="demo_student",
            concept_tag="binary_search_bounds_update",
            is_correct=True,
            time_taken_ms=1800
        )
        att_res = learner_client.record_attempt(att)
        assert att_res.status == "recorded"
        assert att_res.new_mastery_score >= 0.0
        record("Learner: Record Attempt", True, f"Mastery updated to {att_res.new_mastery_score}")
    except Exception as e:
        record("Learner: Record Attempt", False, str(e))

    # 7. Learner Service: Mastery & Weak Concepts
    try:
        mastery = learner_client.get_mastery("demo_student")
        assert "binary_search_bounds_update" in mastery.concept_scores
        weak = learner_client.get_weak_concepts("demo_student")
        assert len(weak.weak_concepts) >= 1
        rec = learner_client.recommend_next("demo_student")
        assert rec.recommended_concept is not None
        record(
            "Learner: Profile & Recommendations",
            True,
            f"Overall={mastery.overall_score}, Weak={len(weak.weak_concepts)}, Recommended='{rec.recommended_concept}'"
        )
    except Exception as e:
        record("Learner: Profile & Recommendations", False, str(e))

    # 8. Assess Service: Quiz Generation
    try:
        q_req = QuizGenerateRequest(
            topic="Binary Search",
            num_questions=3,
            weak_concepts=["binary_search_bounds_update"],
            student_id="demo_student"
        )
        quiz = assess_client.generate_quiz(q_req)
        assert len(quiz.questions) == 3
        record("Assess: Quiz Generation", True, f"Quiz '{quiz.quiz_id}' generated with {len(quiz.questions)} questions")
    except Exception as e:
        record("Assess: Quiz Generation", False, str(e))

    # 9. Assess Service: Flashcards Generation
    try:
        fc_req = FlashcardsGenerateRequest(
            topic="Binary Search",
            count=4,
            weak_concepts=["binary_search_bounds_update"],
            student_id="demo_student"
        )
        fc = assess_client.generate_flashcards(fc_req)
        assert len(fc.cards) == 4
        record("Assess: Flashcards Generation", True, f"{len(fc.cards)} flashcards ready for spaced repetition")
    except Exception as e:
        record("Assess: Flashcards Generation", False, str(e))

    # 10. Assess Service: Quiz Submission & Auto-Grading
    try:
        sub_req = QuizSubmitRequest(
            quiz_id="quiz_bs_101",
            user_id="demo_student",
            answers={"q_bs_1": 0, "q_bs_2": 1, "q_bs_3": 0}  # 2 correct, 1 incorrect
        )
        sub_res = assess_client.submit_quiz(sub_req)
        assert sub_res.total_questions == 3
        assert len(sub_res.feedback) == 3
        record(
            "Assess: Quiz Grading & Feedback",
            True,
            f"Score: {sub_res.score} ({sub_res.correct_count}/{sub_res.total_questions} correct)"
        )
    except Exception as e:
        record("Assess: Quiz Grading & Feedback", False, str(e))

    print("\n" + "=" * 65)
    print("                    E2E TEST SUMMARY MATRIX                    ")
    print("=" * 65)
    print(f"{'Step':<40} | {'Status':<6} | {'Details'}")
    print("-" * 65)
    all_passed = True
    for name, status, detail in results:
        if status != "PASS":
            all_passed = False
        print(f"{name:<40} | {status:<6} | {detail[:40]}")
    print("=" * 65)

    if all_passed:
        print("\n🎉 ALL 10 END-TO-END INTEGRATION STEPS PASSED SUCCESSFULLY!\n")
        return 0
    else:
        print("\n❌ SOME STEPS FAILED. Please review the matrix above.\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_e2e_tests())
