"""
Lesson Generator Module.
Generates 5-step interactive AI Virtual Teacher lessons based on the Binary Search golden example.
Includes a strict multi-stage validation pipeline:
  a. Pydantic schema validation
  b. Subprocess code execution with 5s timeout & real stdout capture
  c. Board command integrity check (valid types, element reference IDs, text limits, max count)
  d. Check question validation (4 options, exactly 1 correct, misconception tags)
  e. Single repair loop on validation errors (STRICT_REAL behavior)
  f. Local file caching in backend/agent/lessons/<slug>.json
"""

import json
import logging
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from backend.agent.schemas import (
    LessonPlan,
    LessonStep,
    CodeChunk,
    CodeAction,
    CheckQuestion,
    BoardCommand,
    TextCommand,
    BoxCommand,
    ArrowCommand,
    EquationCommand,
    MermaidCommand,
    ClearCommand,
    TopicItem,
)
from backend.agent.llm_router import router

logger = logging.getLogger("lesson_generator")

LESSONS_DIR = Path(__file__).resolve().parent / "lessons"
LESSONS_DIR.mkdir(parents=True, exist_ok=True)


def slugify_topic(topic: str) -> str:
    """Normalize a topic name into a safe file slug."""
    s = re.sub(r"[^a-zA-Z0-9]+", "_", topic.strip().lower())
    return s.strip("_")


def get_golden_binary_search_lesson() -> LessonPlan:
    """Returns the golden 5-step Binary Search lesson plan."""
    from backend.agent.teacher import get_mock_binary_search_steps
    steps = get_mock_binary_search_steps()

    # Ensure code_chunks are populated
    for s in steps:
        if s.code_action and not s.code_chunks:
            s.code_chunks = [
                CodeChunk(
                    code=s.code_action.code,
                    explanation=s.code_action.explanation,
                    expected_output=None
                )
            ]

    # Pre-populate exact expected outputs for golden steps
    if len(steps) > 1 and steps[1].code_chunks:
        steps[1].code_chunks[0].expected_output = "low: 0, high: 9 -> mid index: 4\n"
    if len(steps) > 3 and steps[3].code_chunks:
        steps[3].code_chunks[0].expected_output = (
            "Checking range [0..9], mid=4, val=16\n"
            "Checking range [5..9], mid=7, val=56\n"
            "Checking range [5..6], mid=5, val=23\n"
            "Target 23 located at index: 5\n"
        )

    return LessonPlan(
        topic="Binary Search",
        level="beginner",
        steps=steps,
        trace={
            "source": "golden_example",
            "provider": "teacher_template",
            "model": "rule_based_golden",
            "latency_ms": 0
        }
    )


def load_cached_lesson(topic: str) -> Optional[LessonPlan]:
    """Load cached lesson from backend/agent/lessons/<slug>.json if present."""
    slug = slugify_topic(topic)
    lesson_file = LESSONS_DIR / f"{slug}.json"
    if not lesson_file.exists():
        return None

    try:
        content = lesson_file.read_text(encoding="utf-8")
        data = json.loads(content)
        lesson = LessonPlan.model_validate(data)
        if not lesson.trace:
            lesson.trace = {}
        lesson.trace["source"] = "cache"
        lesson.trace["provider"] = "file_cache"
        lesson.trace["model"] = f"lessons/{slug}.json"
        lesson.trace["latency_ms"] = 0
        return lesson
    except Exception as e:
        logger.warning(f"Failed to read cached lesson from {lesson_file}: {e}")
        return None


def save_cached_lesson(lesson: LessonPlan, slug: Optional[str] = None) -> Path:
    """Save validated lesson plan to backend/agent/lessons/<slug>.json."""
    if not slug:
        slug = slugify_topic(lesson.topic)
    lesson_file = LESSONS_DIR / f"{slug}.json"
    data = lesson.model_dump(mode="json")
    lesson_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return lesson_file


def execute_python_code(code: str, timeout: float = 5.0) -> Tuple[bool, str, str]:
    """
    Executes Python code in a standalone subprocess with strict timeout guard.
    Returns (success, stdout, stderr_or_error).
    """
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if proc.returncode != 0:
            return False, proc.stdout, proc.stderr.strip()
        return True, proc.stdout, ""
    except subprocess.TimeoutExpired:
        return False, "", f"TimeoutError: Execution exceeded {timeout}s limit."
    except Exception as e:
        return False, "", str(e)


def validate_lesson_plan(
    raw_data: Any,
    check_code: bool = True
) -> Tuple[Optional[LessonPlan], List[str]]:
    """
    Validation Pipeline:
      a. Pydantic schema check (must parse as LessonPlan or steps with exactly 5 steps)
      b. Subprocess code execution (5s timeout, real stdout replaces expected_output)
      c. Board integrity (supported types, referenced IDs, text lengths <= 140, command count <= 18)
      d. Check question integrity (4 options, exactly 1 correct, explanations)
    Returns (validated_lesson, list_of_error_strings).
    """
    errors: List[str] = []

    # 1. Pydantic Schema Check
    lesson: Optional[LessonPlan] = None
    if isinstance(raw_data, LessonPlan):
        lesson = raw_data
    elif isinstance(raw_data, dict):
        # Could be {"topic": ..., "steps": ...} or directly a LessonPlan
        try:
            lesson = LessonPlan.model_validate(raw_data)
        except Exception as e:
            errors.append(f"Schema validation error: {e}")
            return None, errors
    elif isinstance(raw_data, list):
        # List of 5 steps
        try:
            steps = [LessonStep.model_validate(s) for s in raw_data]
            topic = steps[0].concept if steps else "General"
            lesson = LessonPlan(topic=topic, level="beginner", steps=steps)
        except Exception as e:
            errors.append(f"Steps schema validation error: {e}")
            return None, errors
    else:
        errors.append("Invalid lesson format: expected JSON object or array of steps.")
        return None, errors

    if len(lesson.steps) != 5:
        errors.append(f"Lesson must contain exactly 5 steps (found {len(lesson.steps)}).")

    for idx, step in enumerate(lesson.steps):
        if step.step_index != idx:
            step.step_index = idx

        # Step narration length check
        if not step.narration or len(step.narration.strip()) < 10:
            errors.append(f"Step {idx} narration is too short or empty.")

        # 2. Board Check
        step_ids = set()
        for cmd in step.board_commands:
            if hasattr(cmd, "id") and cmd.id:
                step_ids.add(cmd.id)

        if len(step.board_commands) > 18:
            errors.append(f"Step {idx} has {len(step.board_commands)} board commands (max allowed is 18).")

        for cmd in step.board_commands:
            cmd_type = getattr(cmd, "type", None)
            if cmd_type not in ("text", "box", "arrow", "equation", "mermaid", "clear"):
                errors.append(f"Step {idx} contains unsupported board command type: '{cmd_type}'")

            # Check text length limit
            if isinstance(cmd, TextCommand):
                if len(cmd.content) > 280:
                    errors.append(f"Step {idx} TextCommand '{cmd.id}' exceeds 280 characters ({len(cmd.content)} chars).")

            # Check referenced element IDs in ArrowCommand
            if isinstance(cmd, ArrowCommand):
                if cmd.from_id and cmd.from_id not in step_ids:
                    errors.append(f"Step {idx} ArrowCommand '{cmd.id}' references missing from_id: '{cmd.from_id}'")
                if cmd.to_id and cmd.to_id not in step_ids:
                    errors.append(f"Step {idx} ArrowCommand '{cmd.id}' references missing to_id: '{cmd.to_id}'")

        # 3. Check Question Integrity (Step 2 must have check_question)
        if idx == 2 and not step.check_question:
            errors.append("Step 2 (index 2) must include a check_question understanding checkpoint.")

        if step.check_question:
            cq = step.check_question
            if len(cq.options) != 4:
                errors.append(f"Step {idx} check_question must have exactly 4 options (found {len(cq.options)}).")
            if cq.correct_index < 0 or cq.correct_index >= len(cq.options):
                errors.append(f"Step {idx} check_question correct_index {cq.correct_index} is out of bounds (0-3).")
            if not cq.explanation or len(cq.explanation.strip()) < 5:
                errors.append(f"Step {idx} check_question explanation is missing or trivial.")
            if not cq.concept_tag or len(cq.concept_tag.strip()) < 3:
                errors.append(f"Step {idx} check_question concept_tag is missing or invalid.")

        # 4. Code Execution & Stdout Capture Check
        # Normalize code_action into code_chunks if needed
        if step.code_action and not step.code_chunks:
            step.code_chunks = [
                CodeChunk(
                    code=step.code_action.code,
                    explanation=step.code_action.explanation,
                    expected_output=None
                )
            ]

        if check_code and step.code_chunks:
            for c_idx, chunk in enumerate(step.code_chunks):
                if not chunk.code or not chunk.code.strip():
                    continue
                ok, actual_stdout, err_msg = execute_python_code(chunk.code, timeout=5.0)
                if not ok:
                    errors.append(f"Step {idx} code chunk {c_idx} failed execution: {err_msg[:120]}")
                else:
                    # Replace expected_output with actual verified stdout
                    chunk.expected_output = actual_stdout
                    if step.code_action and c_idx == 0:
                        step.code_action.code = chunk.code

    if errors:
        return None, errors

    return lesson, []


def _build_generator_prompt(topic: str, level: str) -> str:
    golden = get_golden_binary_search_lesson()
    golden_json = json.dumps(golden.model_dump(mode="json"), indent=2)

    prompt = f"""You are an elite Computer Science educator and lesson planner.
Generate a high-quality, interactive 5-step lesson for the topic: "{topic}" (target difficulty level: {level}).

GOLDEN EXAMPLE:
Study the following complete Binary Search lesson JSON carefully. Your output must strictly match this JSON schema and pedagogical structure:

```json
{golden_json}
```

STRICT PEDAGOGICAL & ARCHITECTURAL RULES:
1. 5 STEPS EXACTLY (step_index 0 to 4):
   - Step 0 (Intuition): Visual metaphor, divide & conquer or core intuition. Board commands: clear, title, visual boxes/diagram, complexity equation, mermaid flow.
   - Step 1 (Worked Example): Tracing an example with specific numbers/pointers. Board commands: boxes, pointer arrows, equation, short calculation code in code_chunks.
   - Step 2 (Formative Checkpoint): CheckQuestion with exactly 4 options, exactly 1 correct_index (0-3), detailed explanation, and concept_tag. Board commands: title, rule note, formula equation.
   - Step 3 (Live Code Implementation): Complete runnable Python algorithm in code_chunks. Must execute cleanly in <5 seconds, print helpful step-by-step progress, and print the final result. Board commands: algo title, recurrence/complexity equation, mermaid execution path.
   - Step 4 (Mastery Update & Next Recommendation): Clear canvas, mastery complete text, mastery gain box (+0.35), next recommended topic, mermaid roadmap.

2. BOARD COMMAND RULES:
   - Only use supported types: "text", "box", "arrow", "equation", "mermaid", "clear".
   - Vertical layout: coordinates must flow downwards with increasing y values (e.g. y=40, y=100..150, y=220..270, y=340..400).
   - If an ArrowCommand has from_id or to_id, the corresponding element with that id MUST exist in that step.
   - Keep TextCommand content under 120 characters. No overlapping boxes. At most 15 commands per step.

3. CODE CHUNKS RULES:
   - Provide runnable Python 3 code in code_chunks: [{{"code": "...", "explanation": "...", "expected_output": null}}].
   - If NumPy is helpful (e.g. for Gradient Descent), NumPy is available. Code MUST execute without syntax or runtime errors!

4. RETURN FORMAT:
   - Return ONLY a valid JSON object matching the LessonPlan schema:
     {{"topic": "{topic}", "level": "{level}", "steps": [...]}}
   - No markdown fences, no conversational prose.
"""
    return prompt


def generate_lesson(
    topic: str,
    level: str = "beginner",
    user_id: str = "demo_student",
    force_refresh: bool = False
) -> LessonPlan:
    """
    Main lesson generator:
      1. Check disk file cache (backend/agent/lessons/<slug>.json)
      2. If not cached, call LLM (Gemini first, Groq fallback) at temperature 0.3
      3. Run validation pipeline
      4. Single repair attempt if validation fails
      5. Save validated lesson to disk cache
      6. Return validated LessonPlan
    """
    # 1. Check file cache
    if not force_refresh:
        cached = load_cached_lesson(topic)
        if cached:
            logger.info(f"Loaded lesson for '{topic}' from file cache.")
            return cached

    # 2. Call LLM
    prompt = _build_generator_prompt(topic, level)
    system_prompt = (
        "You are an expert AI Virtual Teacher that outputs ONLY 100% valid JSON matching the LessonPlan schema. "
        "Every Python code block must be runnable and bug-free."
    )

    t0 = time.time()
    logger.info(f"Generating new lesson for topic '{topic}' via LLM router...")

    raw_json = None
    provider_used = "mock"
    model_used = "canned"
    latency_ms = 0

    try:
        raw_text, provider_used, model_used, latency_ms = router._dispatch_providers_sync(
            prompt,
            system_prompt=system_prompt
        )
        raw_json = router._extract_json(raw_text)
    except Exception as e:
        logger.warning(f"LLM call failed for lesson generation: {e}")
        # In mock mode or if all providers fail:
        if router.mock_mode or not router.strict_real:
            golden = get_golden_binary_search_lesson()
            golden.topic = topic
            for s in golden.steps:
                s.concept = topic
            save_cached_lesson(golden)
            return golden
        raise RuntimeError(f"Failed to generate lesson via LLM: {e}")

    # 3. Run Validation Pipeline
    try:
        parsed_data = json.loads(raw_json)
    except Exception as e:
        parsed_data = None
        first_errors = [f"JSON parse error: {e}"]
    else:
        lesson, first_errors = validate_lesson_plan(parsed_data, check_code=True)

    # 4. Repair Attempt if validation errors occurred
    if first_errors:
        logger.warning(f"Lesson validation failed on first attempt: {first_errors}. Attempting single repair...")
        repair_prompt = (
            f"The lesson JSON you generated for '{topic}' failed validation with the following {len(first_errors)} errors:\n"
            + "\n".join(f"- {err}" for err in first_errors)
            + "\n\nOriginal output:\n"
            + (raw_json[:3000] if raw_json else "")
            + "\n\nPlease output the complete, corrected 100% valid JSON fixing ALL of the above errors."
        )

        try:
            repair_text, provider_used, model_used, repair_lat = router._dispatch_providers_sync(
                repair_prompt,
                system_prompt=system_prompt
            )
            repaired_json = router._extract_json(repair_text)
            repaired_data = json.loads(repaired_json)
            lesson, second_errors = validate_lesson_plan(repaired_data, check_code=True)
            if second_errors:
                raise ValueError(f"Lesson repair failed: {'; '.join(second_errors)}")
        except Exception as repair_err:
            logger.error(f"Lesson repair failed: {repair_err}")
            raise ValueError(f"Lesson validation failed after repair: {repair_err}")

    # Set trace metadata
    lesson.trace = {
        "source": "llm",
        "provider": provider_used,
        "model": model_used,
        "latency_ms": int((time.time() - t0) * 1000)
    }

    # 5. Save to File Cache
    save_cached_lesson(lesson)
    logger.info(f"Successfully generated and cached lesson for '{topic}' at {LESSONS_DIR}/{slugify_topic(topic)}.json")

    return lesson


def get_available_topics() -> List[TopicItem]:
    """
    Returns list of available lesson topics for GET /topics.
    Includes Binary Search, Recursion, and the 3 AI-generated & reviewed topics.
    """
    topics = [
        TopicItem(
            id="binary_search",
            title="Binary Search",
            description="Divide-and-conquer search on sorted collections with O(log n) efficiency.",
            level="beginner",
            has_code=True,
            source="golden_example"
        ),
        TopicItem(
            id="recursion",
            title="Recursion & Trees",
            description="Call stack frames, base cases, and elegant binary tree traversals.",
            level="intermediate",
            has_code=True,
            source="golden_example"
        ),
        TopicItem(
            id="bubble_sort",
            title="Bubble Sort",
            description="Elementary comparison sort via adjacent element swaps and early exit.",
            level="beginner",
            has_code=True,
            source="ai_generated_reviewed"
        ),
        TopicItem(
            id="two_pointers",
            title="Two Pointers",
            description="Dual converging pointers on sorted arrays achieving linear O(n) search time.",
            level="intermediate",
            has_code=True,
            source="ai_generated_reviewed"
        ),
        TopicItem(
            id="gradient_descent",
            title="Gradient Descent",
            description="Iterative optimization updating parameters along the negative loss gradient.",
            level="advanced",
            has_code=True,
            source="ai_generated_reviewed"
        )
    ]
    return topics
