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
    detected_misconception: Optional[str] = Field(
        default=None,
        description="Misconception diagnosed from student interaction (e.g. 'confuses midpoint formula with range')"
    )
    remediation: Optional[str] = Field(
        default=None,
        description="Targeted corrective explanation for the identified misconception"
    )
    provider_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadata indicating LLM provider used, latency, and cache status"
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
    last_student_response: Optional[str] = Field(default=None, description="Answer from previous check (e.g. chosen index or text)")
    student_misconceptions: List[str] = Field(
        default_factory=list,
        description="Active misconception tags from learner model"
    )
    feedback: Optional[str] = Field(
        default=None,
        description="Feedback from student, e.g. 'I don\\'t understand'"
    )


class CheckAnswerRequest(BaseModel):
    question_id: str = Field(..., description="ID of question being answered", examples=["bs_check_bounds"])
    selected_index: int = Field(..., description="Option index selected by student (0-3)", examples=[0])
    concept: str = Field(default="Binary Search", description="Concept topic")
    student_id: str = Field(default="demo_student", description="Student ID")


class CheckAnswerResponse(BaseModel):
    is_correct: bool = Field(..., description="Whether selection was correct")
    correct_index: int = Field(..., description="The actual correct index")
    explanation: str = Field(..., description="Explanation of the correct answer")
    detected_misconception: Optional[str] = Field(
        default=None,
        description="Diagnosed misconception tag if student answered incorrectly",
        examples=["confuses_search_direction_when_target_is_greater"]
    )
    remediation: Optional[str] = Field(
        default=None,
        description="Targeted corrective explanation for the UI to display"
    )
    updated_mastery_score: float = Field(..., description="New mastery score after attempt recording", examples=[0.55])
    suggested_board_commands: List[BoardCommand] = Field(
        default_factory=list,
        description="Whiteboard corrective annotations"
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


# --- Learner API Contract Schemas (Person 4) ---

class AttemptRecordRequest(BaseModel):
    user_id: str = Field(default="demo_student", description="Unique student ID", examples=["demo_student"])
    concept_tag: str = Field(..., description="Concept tag for mastery tracking", examples=["binary_search_bounds_update"])
    is_correct: bool = Field(..., description="Whether answer was correct", examples=[False])
    time_spent_seconds: float = Field(default=15.0, description="Time spent on question in seconds", examples=[12.5])
    misconceptions: List[str] = Field(default_factory=list, description="Identified misconception tags", examples=["confuses_low_with_high_shift"])
    question_id: Optional[str] = Field(default=None, description="Associated question ID", examples=["bs_check_bounds"])
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary event metadata")


class AttemptRecordResponse(BaseModel):
    status: str = Field(default="recorded", description="Status code", examples=["recorded"])
    user_id: str = Field(..., description="Student ID", examples=["demo_student"])
    concept_tag: str = Field(..., description="Concept updated", examples=["binary_search_bounds_update"])
    new_mastery_score: float = Field(..., description="Updated mastery score (0.0 to 1.0)", examples=[0.65])
    updated_at: str = Field(default="2026-11-05T19:30:00Z", description="Timestamp")


class MasteryResponse(BaseModel):
    user_id: str = Field(..., description="Student ID", examples=["demo_student"])
    overall_score: float = Field(..., description="Overall weighted mastery (0.0 - 1.0)", examples=[0.72])
    concept_scores: Dict[str, float] = Field(
        ...,
        description="Dictionary mapping concept tags to scores",
        examples=[{"binary_search_intuition": 0.90, "binary_search_bounds_update": 0.45, "binary_search_complexity": 0.80}]
    )
    attempt_counts: Dict[str, int] = Field(
        ...,
        description="Number of attempts per concept",
        examples=[{"binary_search_intuition": 3, "binary_search_bounds_update": 2, "binary_search_complexity": 1}]
    )
    last_active: str = Field(default="2026-11-05T19:30:00Z", description="Last activity timestamp")


class WeakConceptItem(BaseModel):
    concept_tag: str = Field(..., description="Concept tag", examples=["binary_search_bounds_update"])
    mastery_score: float = Field(..., description="Current mastery score", examples=[0.45])
    active_misconceptions: List[str] = Field(
        default_factory=list,
        description="Observed misconceptions",
        examples=["confuses_low_with_high_shift"]
    )
    recommended_action: str = Field(
        default="Review midpoint shift rules with interactive check",
        description="Remediation suggestion"
    )


class WeakConceptsResponse(BaseModel):
    user_id: str = Field(..., description="Student ID", examples=["demo_student"])
    weak_concepts: List[WeakConceptItem] = Field(..., description="List of weak concepts with score < 0.60")


class RecommendResponse(BaseModel):
    user_id: str = Field(..., description="Student ID", examples=["demo_student"])
    recommended_concept: str = Field(..., description="Concept to study next", examples=["binary_search_bounds_update"])
    reason: str = Field(..., description="Pedagogical rationale", examples=["Low mastery score (0.45) on recent checkpoint"])
    suggested_action: Literal["lesson", "quiz", "flashcard"] = Field(
        default="lesson",
        description="Recommended mode of practice",
        examples=["lesson"]
    )


# --- Assess API Contract Schemas (Person 3) ---

class QuizGenerateRequest(BaseModel):
    topic: str = Field(default="Binary Search", description="Quiz topic", examples=["Binary Search"])
    num_questions: int = Field(default=3, description="Number of questions to generate", examples=[3])
    difficulty: Literal["beginner", "intermediate", "advanced"] = Field(
        default="beginner",
        description="Difficulty level",
        examples=["beginner"]
    )
    weak_concepts: List[str] = Field(
        default_factory=list,
        description="Target specific weak concepts",
        examples=["binary_search_bounds_update"]
    )


class QuizQuestionItem(BaseModel):
    question_id: str = Field(..., description="Unique question ID", examples=["q_bs_1"])
    concept_tag: str = Field(..., description="Target concept tag", examples=["binary_search_bounds_update"])
    question: str = Field(..., description="Question prompt", examples=["When target > arr[mid], how should bounds update?"])
    options: List[str] = Field(
        ...,
        description="Answer options",
        examples=[["high = mid - 1", "low = mid + 1", "low = mid", "high = mid"]]
    )
    correct_index: int = Field(..., description="Zero-based index of correct answer", examples=[1])
    explanation: str = Field(
        ...,
        description="Explanation of correct option",
        examples=["Because array is sorted and target is larger, target lies in right half: low = mid + 1."]
    )


class QuizGenerateResponse(BaseModel):
    quiz_id: str = Field(..., description="Quiz instance ID", examples=["quiz_bs_101"])
    topic: str = Field(..., description="Topic name", examples=["Binary Search"])
    questions: List[QuizQuestionItem] = Field(..., description="List of generated quiz questions")


class FlashcardItem(BaseModel):
    card_id: str = Field(..., description="Unique flashcard ID", examples=["fc_bs_1"])
    concept_tag: str = Field(..., description="Associated concept tag", examples=["binary_search_complexity"])
    front: str = Field(..., description="Front of flashcard (Prompt/Question)", examples=["What is the time complexity of Binary Search?"])
    back: str = Field(..., description="Back of flashcard (Answer)", examples=["O(log n) because the search space halves every iteration."])
    hint: Optional[str] = Field(default=None, description="Optional hint", examples=["Think of dividing n by 2 repeatedly."])


class FlashcardsGenerateRequest(BaseModel):
    topic: str = Field(default="Binary Search", description="Flashcard deck topic", examples=["Binary Search"])
    count: int = Field(default=4, description="Number of cards to produce", examples=[4])
    concept_tags: List[str] = Field(
        default_factory=list,
        description="Specific concept tags",
        examples=["binary_search_complexity", "binary_search_precondition"]
    )


class FlashcardsGenerateResponse(BaseModel):
    topic: str = Field(..., description="Topic of cards", examples=["Binary Search"])
    cards: List[FlashcardItem] = Field(..., description="Deck of flashcards")


class QuizSubmitRequest(BaseModel):
    quiz_id: str = Field(..., description="Quiz ID", examples=["quiz_bs_101"])
    user_id: str = Field(default="demo_student", description="Student ID", examples=["demo_student"])
    answers: Dict[str, int] = Field(
        ...,
        description="Map of question_id to selected option index",
        examples=[{"q_bs_1": 1, "q_bs_2": 0}]
    )


class QuestionResultFeedback(BaseModel):
    question_id: str
    concept_tag: str
    is_correct: bool
    selected_index: int
    correct_index: int
    explanation: str
    identified_misconception: Optional[str] = None


class QuizSubmitResponse(BaseModel):
    quiz_id: str
    user_id: str
    score: float = Field(..., description="Score fraction between 0.0 and 1.0", examples=[1.0])
    total_questions: int = Field(..., examples=[2])
    correct_count: int = Field(..., examples=[2])
    feedback: List[QuestionResultFeedback] = Field(..., description="Detailed feedback per question")

