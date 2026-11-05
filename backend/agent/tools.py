from typing import Any, Dict, List, Optional
from backend.agent.schemas import (
    BoardCommand,
    CheckQuestion,
    CodeAction,
    ToolCallRecord,
    AttemptRecordRequest,
    QuizGenerateRequest,
)
from backend.agent.client import learner_client, assess_client
import logging

logger = logging.getLogger("agent_tools")


class AgentTools:
    """
    Teacher agent tools callable during lesson planning and execution.
    These tools return structured representations and call contracted services
    (learner model, assess engine) with automatic mock fallbacks.
    """

    @staticmethod
    def draw_on_board(commands: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Draw elements (text, boxes, arrows, LaTeX equations, Mermaid diagrams) on the board."""
        return {
            "status": "success",
            "commands_count": len(commands),
            "command_types": [cmd.get("type") if isinstance(cmd, dict) else getattr(cmd, "type", "unknown") for cmd in commands]
        }

    @staticmethod
    def run_code(code: str, language: str = "python") -> Dict[str, Any]:
        """Simulate or execute Python snippet in live coding environment."""
        return {
            "status": "prepared_for_live_coding",
            "language": language,
            "code_length": len(code),
        }

    @staticmethod
    def ask_check_question(
        question_id: str,
        question: str,
        options: List[str],
        correct_index: int,
        explanation: str,
        concept_tag: str
    ) -> Dict[str, Any]:
        """Present a checkpoint question to assess student understanding before advancing."""
        return {
            "status": "question_created",
            "question_id": question_id,
            "concept_tag": concept_tag
        }

    @staticmethod
    def generate_quiz(topic: str, num_questions: int = 3, difficulty: str = "beginner", weak_concepts: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate targeted quiz for concept practice by calling Assess API thin client."""
        req = QuizGenerateRequest(
            topic=topic or "Binary Search",
            num_questions=num_questions or 3,
            difficulty=difficulty or "beginner",
            weak_concepts=weak_concepts or []
        )
        res = assess_client.generate_quiz(req)
        return res.model_dump()

    @staticmethod
    def update_mastery(student_id: str, concept: str, score_delta: float, is_correct: bool = True, misconceptions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Notify learner model of updated mastery score by calling Learner API thin client."""
        req = AttemptRecordRequest(
            user_id=student_id or "demo_student",
            concept_tag=concept or "binary_search_bounds_update",
            is_correct=is_correct,
            misconceptions=misconceptions or []
        )
        res = learner_client.record_attempt(req)
        return res.model_dump()

    @staticmethod
    def recommend_next(student_id: str, weak_concepts: Optional[List[str]] = None) -> Dict[str, Any]:
        """Recommend next concept or practice activity based on learner model."""
        res = learner_client.recommend_next(student_id or "demo_student")
        return res.model_dump()


def execute_tool_call(tool_name: str, params: Dict[str, Any]) -> ToolCallRecord:
    tools_map = {
        "draw_on_board": lambda p: AgentTools.draw_on_board(p.get("commands", [])),
        "run_code": lambda p: AgentTools.run_code(p.get("code", ""), p.get("language", "python")),
        "ask_check_question": lambda p: AgentTools.ask_check_question(
            p.get("question_id", "chk_1"),
            p.get("question", ""),
            p.get("options", []),
            p.get("correct_index", 0),
            p.get("explanation", ""),
            p.get("concept_tag", "general")
        ),
        "generate_quiz": lambda p: AgentTools.generate_quiz(
            p.get("topic", "Binary Search"),
            p.get("num_questions", 3),
            p.get("difficulty", "beginner"),
            p.get("weak_concepts", [])
        ),
        "update_mastery": lambda p: AgentTools.update_mastery(
            p.get("student_id", "demo_student"),
            p.get("concept", "binary_search_bounds_update"),
            p.get("score_delta", 0.1),
            p.get("is_correct", p.get("is_correct", True)),
            p.get("misconceptions", p.get("misconceptions", []))
        ),
        "recommend_next": lambda p: AgentTools.recommend_next(
            p.get("student_id", "demo_student"),
            p.get("weak_concepts", [])
        )
    }

    if tool_name not in tools_map:
        return ToolCallRecord(
            tool_name=tool_name,
            parameters=params,
            result={"error": f"Unknown tool: {tool_name}"}
        )

    try:
        res = tools_map[tool_name](params)
        return ToolCallRecord(tool_name=tool_name, parameters=params, result=res)
    except Exception as e:
        logger.exception(f"Tool execution failed for {tool_name}")
        return ToolCallRecord(tool_name=tool_name, parameters=params, result={"error": str(e)})
