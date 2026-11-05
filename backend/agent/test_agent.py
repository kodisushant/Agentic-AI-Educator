import json
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from backend.agent.schemas import (
    LessonStep,
    LessonStepRequest,
    ChatMessageRequest,
    ChatMessageResponse,
    ToolCallRequest,
    ToolCallRecord,
    TextCommand,
    BoxCommand,
    ArrowCommand,
    EquationCommand,
    MermaidCommand,
    ClearCommand,
    AttemptRecordRequest,
    QuizGenerateRequest,
    FlashcardsGenerateRequest,
    QuizSubmitRequest,
    CheckAnswerRequest,
    CheckAnswerResponse,
)
from backend.agent.teacher import teacher_agent, get_mock_binary_search_steps
from backend.agent.tools import execute_tool_call
from backend.agent.client import learner_client, assess_client


def run_unit_tests():
    print("=== Running Agent Synchronous Unit Tests ===", flush=True)

    # 1. Test Mock Steps structure and validation
    steps = get_mock_binary_search_steps()
    assert len(steps) == 5, f"Expected 5 steps, got {len(steps)}"
    print(f"✓ Retrieved {len(steps)} mock lesson steps", flush=True)

    from backend.agent.teacher import get_mock_recursion_steps
    rec_steps = get_mock_recursion_steps()
    assert len(rec_steps) == 5
    rec_step_0 = teacher_agent.get_next_step_sync(LessonStepRequest(concept="Recursion", step_index=0))
    assert rec_step_0.step_id == "rec_step_0"
    print("✓ Retrieved 5 mock recursion steps & dynamic dispatch verified", flush=True)

    for i, step in enumerate(steps):
        assert step.step_index == i
        assert step.concept == "Binary Search"
        assert len(step.narration) > 10
        step_json = step.model_dump_json()
        validated = LessonStep.model_validate_json(step_json)
        assert validated.step_id == step.step_id
    print("✓ All 5 lesson steps validated against Pydantic schema", flush=True)

    # 2. Check board command polymorphism (discriminator = 'type')
    commands = steps[0].board_commands
    cmd_types = {cmd.type for cmd in commands}
    assert "clear" in cmd_types
    assert "text" in cmd_types
    assert "box" in cmd_types
    assert "arrow" in cmd_types
    assert "equation" in cmd_types
    assert "mermaid" in cmd_types
    print(f"✓ Polymorphic board commands verified: {cmd_types}", flush=True)

    # 3. Test CheckQuestion in Step 2
    step2 = steps[2]
    assert step2.check_question is not None
    assert step2.check_question.correct_index == 1
    assert len(step2.check_question.options) == 4
    print("✓ Step 2 CheckQuestion verified", flush=True)

    # 4. Test CodeAction in Step 3
    step3 = steps[3]
    assert step3.code_action is not None
    assert "def binary_search" in step3.code_action.code
    assert step3.code_action.action == "execute"
    print("✓ Step 3 CodeAction verified", flush=True)

    # 5. Test Tools through execute_tool_call
    rec1 = execute_tool_call("draw_on_board", {"commands": [{"type": "text", "content": "hi"}]})
    assert rec1.result["status"] == "success"

    rec2 = execute_tool_call("run_code", {"code": "print(123)", "language": "python"})
    assert rec2.result["status"] == "prepared_for_live_coding"

    rec3 = execute_tool_call("ask_check_question", {
        "question_id": "q1",
        "question": "Sample?",
        "options": ["A", "B"],
        "correct_index": 0,
        "explanation": "Exp",
        "concept_tag": "tag1"
    })
    assert rec3.result["status"] == "question_created"

    rec4 = execute_tool_call("generate_quiz", {"topic": "Binary Search", "num_questions": 2})
    assert "quiz_id" in rec4.result
    assert len(rec4.result["questions"]) == 2

    rec5 = execute_tool_call("update_mastery", {"student_id": "std_1", "concept": "bs", "score_delta": 0.2})
    assert rec5.result["status"] == "recorded"

    rec6 = execute_tool_call("recommend_next", {"student_id": "std_1"})
    assert "recommended_concept" in rec6.result
    print("✓ All 6 teacher tool executions verified", flush=True)

    # 6. Test Learner thin client
    att_res = learner_client.record_attempt(AttemptRecordRequest(
        user_id="demo_student",
        concept_tag="binary_search_bounds_update",
        is_correct=True
    ))
    assert att_res.status == "recorded"
    assert att_res.new_mastery_score >= 0.0

    mastery_res = learner_client.get_mastery("demo_student")
    assert "binary_search_bounds_update" in mastery_res.concept_scores

    weak_res = learner_client.get_weak_concepts("demo_student")
    assert len(weak_res.weak_concepts) >= 1

    rec_res = learner_client.recommend_next("demo_student")
    assert rec_res.recommended_concept is not None
    print("✓ LearnerClient (record_attempt, get_mastery, get_weak_concepts, recommend_next) verified", flush=True)

    # 7. Test Assess thin client
    quiz_res = assess_client.generate_quiz(QuizGenerateRequest(topic="Binary Search", num_questions=2))
    assert len(quiz_res.questions) == 2

    fc_res = assess_client.generate_flashcards(FlashcardsGenerateRequest(topic="Binary Search", count=3))
    assert len(fc_res.cards) == 3

    answers = {q.question_id: q.correct_index for q in quiz_res.questions}
    sub_res = assess_client.submit_quiz(QuizSubmitRequest(
        quiz_id=quiz_res.quiz_id,
        user_id="demo_student",
        answers=answers
    ))
    assert sub_res.score == 1.0
    print("✓ AssessClient (generate_quiz, generate_flashcards, submit_quiz) verified", flush=True)

    # 8. Test Checkpoint Answer Diagnosis and Misconception Classification
    wrong_chk = teacher_agent.evaluate_check_answer(CheckAnswerRequest(
        question_id="bs_check_bounds",
        selected_index=0,
        concept="Binary Search",
        student_id="demo_student"
    ))
    assert not wrong_chk.is_correct
    assert wrong_chk.detected_misconception == "confuses_direction_when_target_greater"
    assert wrong_chk.remediation is not None
    assert len(wrong_chk.remediation) > 10
    print(f"✓ Checkpoint wrong answer diagnosed: {wrong_chk.detected_misconception}", flush=True)

    correct_chk = teacher_agent.evaluate_check_answer(CheckAnswerRequest(
        question_id="bs_check_bounds",
        selected_index=1,
        concept="Binary Search",
        student_id="demo_student"
    ))
    assert correct_chk.is_correct
    print("✓ Checkpoint correct answer verified", flush=True)

    # 9. Test Adaptive Step Generation upon Wrong Student Answer
    step_remed = teacher_agent.get_next_step_sync(LessonStepRequest(
        concept="Binary Search",
        student_id="demo_student",
        step_index=2,
        last_student_response="0"
    ))
    assert step_remed.detected_misconception is not None
    assert step_remed.remediation is not None
    assert "search direction" in step_remed.narration.lower() or "noticed" in step_remed.narration.lower()
    print(f"✓ Adaptive remediation step generated with exposed misconception: '{step_remed.detected_misconception}'", flush=True)

    # 10. Verify Contract files exist and are valid JSON
    contracts_dir = root_dir / "contracts"
    bc_file = contracts_dir / "board_commands.json"
    openapi_file = contracts_dir / "openapi.json"
    assert bc_file.exists(), "board_commands.json missing"
    assert openapi_file.exists(), "openapi.json missing"

    with open(bc_file, "r", encoding="utf-8") as f:
        bc_data = json.load(f)
        assert "$defs" in bc_data
        assert "LessonStep" in bc_data["$defs"]

    with open(openapi_file, "r", encoding="utf-8") as f:
        oa_data = json.load(f)
        assert "paths" in oa_data
        # Verify required contract endpoints
        assert "/lesson/step" in oa_data["paths"]
        assert "/learner/attempt" in oa_data["paths"]
        assert "/learner/mastery/{user_id}" in oa_data["paths"]
        assert "/learner/weak/{user_id}" in oa_data["paths"]
        assert "/learner/recommend/{user_id}" in oa_data["paths"]
        assert "/assess/quiz" in oa_data["paths"]
        assert "/assess/flashcards" in oa_data["paths"]
        assert "/assess/submit" in oa_data["paths"]

    print("✓ All contracted paths verified in openapi.json", flush=True)
    print("\nAll mock unit tests passed successfully!", flush=True)

    # 11. Conditional Real LLM Testing (Run only when REAL_LLM=1)
    if os.getenv("REAL_LLM") == "1":
        print("\n=== Running REAL_LLM=1 Provider Tests ===", flush=True)
        from backend.agent.test_real_llm import run_provider_tests
        run_provider_tests()


if __name__ == "__main__":
    import os
    run_unit_tests()
