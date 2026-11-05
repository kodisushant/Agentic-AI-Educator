import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from backend.agent.schemas import (
    BoardCommand,
    TextCommand,
    BoxCommand,
    ArrowCommand,
    EquationCommand,
    MermaidCommand,
    ClearCommand,
    LessonStep,
    LessonStepRequest,
    ChatMessageRequest,
    ChatMessageResponse,
    CheckQuestion,
    CodeAction,
)
from backend.agent.main import app
from pydantic import TypeAdapter


def export_contracts():
    contracts_dir = root_dir / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)

    # 1. Export JSON Schema for board commands and lesson steps
    board_adapter = TypeAdapter(BoardCommand)
    step_adapter = TypeAdapter(LessonStep)

    combined_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "AITeacherWhiteboardAndLessonSchema",
        "description": "Contracts for whiteboard drawing commands and lesson step payloads",
        "$defs": {
            "TextCommand": TextCommand.model_json_schema(),
            "BoxCommand": BoxCommand.model_json_schema(),
            "ArrowCommand": ArrowCommand.model_json_schema(),
            "EquationCommand": EquationCommand.model_json_schema(),
            "MermaidCommand": MermaidCommand.model_json_schema(),
            "ClearCommand": ClearCommand.model_json_schema(),
            "CodeAction": CodeAction.model_json_schema(),
            "CheckQuestion": CheckQuestion.model_json_schema(),
            "LessonStep": LessonStep.model_json_schema(),
            "LessonStepRequest": LessonStepRequest.model_json_schema(),
            "ChatMessageRequest": ChatMessageRequest.model_json_schema(),
            "ChatMessageResponse": ChatMessageResponse.model_json_schema(),
        },
        "properties": {
            "board_command": board_adapter.json_schema(),
            "lesson_step": step_adapter.json_schema(),
        }
    }

    schema_file = contracts_dir / "board_commands.json"
    with open(schema_file, "w", encoding="utf-8") as f:
        json.dump(combined_schema, f, indent=2)
    print(f"Exported JSON Schema: {schema_file}")

    # 2. Export OpenAPI JSON Specification
    openapi_schema = app.openapi()
    openapi_file = contracts_dir / "openapi.json"
    with open(openapi_file, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"Exported OpenAPI spec: {openapi_file}")


if __name__ == "__main__":
    export_contracts()
