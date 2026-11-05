from __future__ import annotations
from typing import Annotated, Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


# --- Whiteboard Commands ---

class TextCommand(BaseModel):
    type: Literal["text"] = "text"
    id: str = Field(..., description="Unique identifier for the board element")
    content: str = Field(..., description="Text content to display")
    x: float = Field(..., description="X coordinate on whiteboard canvas")
    y: float = Field(..., description="Y coordinate on whiteboard canvas")
    size: Optional[int] = Field(default=18, description="Font size in pixels")
    color: Optional[str] = Field(default="#1e293b", description="Hex color string")


class BoxCommand(BaseModel):
    type: Literal["box"] = "box"
    id: str = Field(..., description="Unique identifier for the board element")
    label: Optional[str] = Field(default=None, description="Label or value inside the box")
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    width: float = Field(default=80.0, description="Width in pixels")
    height: float = Field(default=50.0, description="Height in pixels")
    color: Optional[str] = Field(default="#2563eb", description="Border color")
    fill: Optional[str] = Field(default="#eff6ff", description="Background fill color")


class ArrowCommand(BaseModel):
    type: Literal["arrow"] = "arrow"
    id: str = Field(..., description="Unique identifier for the board element")
    from_id: Optional[str] = Field(default=None, description="Source element ID")
    to_id: Optional[str] = Field(default=None, description="Target element ID")
    start_x: Optional[float] = Field(default=None, description="Start X if not binding to element")
    start_y: Optional[float] = Field(default=None, description="Start Y if not binding to element")
    end_x: Optional[float] = Field(default=None, description="End X if not binding to element")
    end_y: Optional[float] = Field(default=None, description="End Y if not binding to element")
    label: Optional[str] = Field(default=None, description="Optional label along the arrow")
    color: Optional[str] = Field(default="#0284c7", description="Arrow stroke color")


class EquationCommand(BaseModel):
    type: Literal["equation"] = "equation"
    id: str = Field(..., description="Unique identifier for the board element")
    latex: str = Field(..., description="LaTeX formula string, rendered with KaTeX")
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    label: Optional[str] = Field(default=None, description="Caption or description")


class MermaidCommand(BaseModel):
    type: Literal["mermaid"] = "mermaid"
    id: str = Field(..., description="Unique identifier for the board element")
    chart: str = Field(..., description="Mermaid diagram definition string")
    x: float = Field(default=50.0, description="X coordinate")
    y: float = Field(default=100.0, description="Y coordinate")
    title: Optional[str] = Field(default=None, description="Diagram title")


class ClearCommand(BaseModel):
    type: Literal["clear"] = "clear"
    id: str = Field(default="clear_all", description="Clear canvas marker")


BoardCommand = Annotated[
    Union[TextCommand, BoxCommand, ArrowCommand, EquationCommand, MermaidCommand, ClearCommand],
    Field(discriminator="type")
]


# --- Live Coding & Assessment Schemas ---

class CodeAction(BaseModel):
    code: str = Field(..., description="Python code block")
    language: str = Field(default="python", description="Language for Monaco editor")
    action: Literal["display", "type", "execute", "explain"] = Field(
        default="execute",
        description="Live coding mode behavior"
    )
    explanation: Optional[str] = Field(default=None, description="Code explanation or comments")


class CheckQuestion(BaseModel):
    question_id: str = Field(..., description="Unique question identifier")
    question: str = Field(..., description="The multiple choice question")
    options: List[str] = Field(..., description="4 candidate answers")
    correct_index: int = Field(..., description="Index of correct answer (0-3)")
    explanation: str = Field(..., description="Explanation of why this answer is correct")
    concept_tag: str = Field(..., description="Concept tag for mastery tracking (e.g. 'midpoint_calc')")


class ToolCallRecord(BaseModel):
    tool_name: str = Field(..., description="Name of the tool called")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Arguments supplied to the tool")
    result: Optional[Any] = Field(default=None, description="Result returned from the tool")


# --- Lesson Step & Interaction Schemas ---

class LessonStep(BaseModel):
    step_id: str = Field(..., description="Unique ID for this teaching step")
    step_index: int = Field(..., description="0-based sequence number")
    total_steps: int = Field(default=5, description="Expected total steps in the lesson")
    concept: str = Field(..., description="Teaching topic, e.g. 'Binary Search'")
    narration: str = Field(..., description="Spoken/caption explanation from teacher")
    board_commands: List[BoardCommand] = Field(
        default_factory=list,
        description="Whiteboard draw commands for this step"
    )
    code_action: Optional[CodeAction] = Field(
        default=None,
        description="Code to display or execute in Monaco/Pyodide"
    )
    check_question: Optional[CheckQuestion] = Field(
        default=None,
        description="Interactive understanding check question"
    )
    agent_thoughts: Optional[str] = Field(
        default=None,
        description="Visible reasoning trace showing agentic logic"
    )
    tool_calls: List[ToolCallRecord] = Field(
        default_factory=list,
        description="Tools invoked by the agent to construct this step"
    )
    is_final_step: bool = Field(default=False, description="True if lesson ends at this step")


class LessonStepRequest(BaseModel):
    concept: str = Field(default="Binary Search", description="Concept name to teach")
    student_id: str = Field(default="demo_student", description="ID of active learner")
    step_index: int = Field(default=0, description="Step requested")
    last_student_response: Optional[str] = Field(default=None, description="Answer from previous check")
    student_misconceptions: List[str] = Field(
        default_factory=list,
        description="Active misconception tags from learner model"
    )
    feedback: Optional[str] = Field(
        default=None,
        description="Feedback from student, e.g. 'I don\\'t understand'"
    )


class ChatMessageRequest(BaseModel):
    student_id: str = Field(default="demo_student", description="ID of student")
    concept: str = Field(default="Binary Search", description="Current lesson topic")
    message: str = Field(..., description="Student chat message or question")
    current_step_index: int = Field(default=0, description="Current step in lesson")


class ChatMessageResponse(BaseModel):
    reply: str = Field(..., description="Teacher's conversational reply")
    suggested_board_commands: List[BoardCommand] = Field(
        default_factory=list,
        description="Optional board highlights answering the query"
    )
    agent_thoughts: Optional[str] = Field(
        default=None,
        description="Reasoning trace for how the teacher formulated the answer"
    )


# --- Tool Loop Direct Schemas ---

class ToolCallRequest(BaseModel):
    tool_name: Literal[
        "draw_on_board",
        "run_code",
        "ask_check_question",
        "generate_quiz",
        "update_mastery",
        "recommend_next"
    ]
    parameters: Dict[str, Any]
