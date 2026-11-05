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
)
from backend.agent.teacher import get_mock_binary_search_steps
from backend.agent.tools import execute_tool_call


def run_unit_tests():
    print("=== Running Agent Synchronous Unit Tests ===", flush=True)

    # 1. Test Mock Steps structure and validation
    steps = get_mock_binary_search_steps()
    assert len(steps) == 5, f"Expected 5 steps, got {len(steps)}"
    print(f"✓ Retrieved {len(steps)} mock lesson steps", flush=True)

    for i, step in enumerate(steps):
        assert step.step_index == i
        assert step.concept == "Binary Search"
        assert len(step.narration) > 10
        # Check Pydantic serialization roundtrip
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

    # 5. Test Tool executions
    tools_to_test = [
        ("draw_on_board", {"commands": [{"type": "text", "content": "hi"}]}),
        ("run_code", {"code": "print(123)", "language": "python"}),
        ("ask_check_question", {
            "question_id": "q1",
            "question": "Sample?",
            "options": ["A", "B"],
            "correct_index": 0,
            "explanation": "Exp",
            "concept_tag": "tag1"
        }),
        ("generate_quiz", {"topic": "Binary Search", "num_questions": 2}),
        ("update_mastery", {"student_id": "std_1", "concept": "bs", "score_delta": 0.2}),
        ("recommend_next", {"student_id": "std_1", "weak_concepts": ["edge_cases"]}),
    ]

    for tool_name, params in tools_to_test:
        rec = execute_tool_call(tool_name, params)
        assert rec.tool_name == tool_name
        assert "status" in rec.result or "commands_count" in rec.result
        print(f"✓ Tool '{tool_name}' verified: {rec.result}", flush=True)

    # 6. Verify Contract files exist and are valid JSON
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
        assert "/lesson/step" in oa_data["paths"]
        assert "/mock/lesson" in oa_data["paths"]

    print("✓ Contracts board_commands.json and openapi.json are valid", flush=True)
    print("\nAll unit tests passed successfully!", flush=True)


if __name__ == "__main__":
    run_unit_tests()
