import json
from typing import Dict, List, Optional
from backend.agent.schemas import (
    BoardCommand,
    TextCommand,
    BoxCommand,
    ArrowCommand,
    EquationCommand,
    MermaidCommand,
    ClearCommand,
    CodeAction,
    CheckQuestion,
    LessonStep,
    LessonStepRequest,
    ChatMessageRequest,
    ChatMessageResponse,
    ToolCallRecord,
)
from backend.agent.llm_router import router
from backend.agent.tools import execute_tool_call


def get_mock_binary_search_steps() -> List[LessonStep]:
    """Generates the canned 5-step interactive lesson on Binary Search."""
    steps = [
        # Step 0: Intuition & Divide and Conquer
        LessonStep(
            step_id="bs_step_0",
            step_index=0,
            total_steps=5,
            concept="Binary Search",
            narration=(
                "Welcome to Binary Search! Imagine searching for a contact in a phonebook of 1,000 pages. "
                "Instead of reading page by page, you flip straight to the middle. "
                "Depending on alphabetical order, you instantly eliminate 500 pages. "
                "Binary search repeatedly cuts our search space in half with every single check, "
                "turning an O(n) scan into an ultrafast O(log n) search!"
            ),
            agent_thoughts="Goal: Introduce intuition of divide-and-conquer using visual phonebook/array metaphor.",
            board_commands=[
                ClearCommand(id="clear_0"),
                TextCommand(
                    id="title_text",
                    content="Binary Search: Divide & Conquer",
                    x=60,
                    y=40,
                    size=24,
                    color="#0f172a"
                ),
                TextCommand(
                    id="array_label",
                    content="Sorted Array (n = 10):",
                    x=60,
                    y=100,
                    size=16,
                    color="#475569"
                ),
                # Visual Array Boxes
                BoxCommand(id="box_0", label="2", x=60, y=130, width=55, height=50, color="#3b82f6", fill="#eff6ff"),
                BoxCommand(id="box_1", label="5", x=125, y=130, width=55, height=50, color="#3b82f6", fill="#eff6ff"),
                BoxCommand(id="box_2", label="8", x=190, y=130, width=55, height=50, color="#3b82f6", fill="#eff6ff"),
                BoxCommand(id="box_3", label="12", x=255, y=130, width=55, height=50, color="#3b82f6", fill="#eff6ff"),
                BoxCommand(id="box_4", label="16", x=320, y=130, width=55, height=50, color="#3b82f6", fill="#eff6ff"),
                BoxCommand(id="box_5", label="23", x=385, y=130, width=55, height=50, color="#3b82f6", fill="#eff6ff"),
                BoxCommand(id="box_6", label="38", x=450, y=130, width=55, height=50, color="#3b82f6", fill="#eff6ff"),
                BoxCommand(id="box_7", label="56", x=515, y=130, width=55, height=50, color="#3b82f6", fill="#eff6ff"),
                BoxCommand(id="box_8", label="72", x=580, y=130, width=55, height=50, color="#3b82f6", fill="#eff6ff"),
                BoxCommand(id="box_9", label="91", x=645, y=130, width=55, height=50, color="#3b82f6", fill="#eff6ff"),
                # Low and High pointers
                ArrowCommand(id="arr_low", start_x=87, start_y=230, end_x=87, end_y=190, label="low = 0", color="#16a34a"),
                ArrowCommand(id="arr_high", start_x=672, start_y=230, end_x=672, end_y=190, label="high = 9", color="#dc2626"),
                EquationCommand(
                    id="eq_complexity",
                    latex=r"\mathcal{O}(\log_2 n) \ll \mathcal{O}(n)",
                    x=60,
                    y=270,
                    label="Logarithmic vs Linear Time Complexity"
                ),
                MermaidCommand(
                    id="flow_overview",
                    chart="graph LR\n  A[Sorted Array] --> B[Check Midpoint]\n  B -->|Target == Mid| C[Found!]\n  B -->|Target < Mid| D[Search Left Half]\n  B -->|Target > Mid| E[Search Right Half]",
                    x=60,
                    y=340,
                    title="Binary Search Flowchart"
                )
            ],
            tool_calls=[
                execute_tool_call("draw_on_board", {"commands": ["title_text", "boxes_0_9", "eq_complexity", "flow_overview"]})
            ],
            is_final_step=False
        ),

        # Step 1: Calculating Midpoint & Discarding Half
        LessonStep(
            step_id="bs_step_1",
            step_index=1,
            total_steps=5,
            concept="Binary Search",
            narration=(
                "Now let's find the midpoint. With low = 0 and high = 9, our formula is mid = (0 + 9) // 2 = 4. "
                "Looking at index 4, the value is 16. Suppose our target is 23. "
                "Because 23 is greater than 16 and the array is strictly sorted, 23 CANNOT exist anywhere in indices 0 through 4! "
                "We discard the entire left half in one operation."
            ),
            agent_thoughts="Highlighting index 4 (mid). Target is 23. Explaining why elements <= 16 can be discarded.",
            board_commands=[
                # Dim the left half
                BoxCommand(id="box_0", label="2", x=60, y=130, width=55, height=50, color="#cbd5e1", fill="#f1f5f9"),
                BoxCommand(id="box_1", label="5", x=125, y=130, width=55, height=50, color="#cbd5e1", fill="#f1f5f9"),
                BoxCommand(id="box_2", label="8", x=190, y=130, width=55, height=50, color="#cbd5e1", fill="#f1f5f9"),
                BoxCommand(id="box_3", label="12", x=255, y=130, width=55, height=50, color="#cbd5e1", fill="#f1f5f9"),
                # Mid element highlighted in gold
                BoxCommand(id="box_4", label="16", x=320, y=130, width=55, height=50, color="#d97706", fill="#fef3c7"),
                # Active remaining elements
                BoxCommand(id="box_5", label="23", x=385, y=130, width=55, height=50, color="#2563eb", fill="#eff6ff"),
                BoxCommand(id="box_6", label="38", x=450, y=130, width=55, height=50, color="#2563eb", fill="#eff6ff"),
                BoxCommand(id="box_7", label="56", x=515, y=130, width=55, height=50, color="#2563eb", fill="#eff6ff"),
                BoxCommand(id="box_8", label="72", x=580, y=130, width=55, height=50, color="#2563eb", fill="#eff6ff"),
                BoxCommand(id="box_9", label="91", x=645, y=130, width=55, height=50, color="#2563eb", fill="#eff6ff"),
                ArrowCommand(id="arr_mid", start_x=347, start_y=230, end_x=347, end_y=190, label="mid = 4 (val: 16)", color="#d97706"),
                EquationCommand(
                    id="eq_mid",
                    latex=r"mid = \lfloor \frac{low + high}{2} \rfloor = \lfloor \frac{0 + 9}{2} \rfloor = 4",
                    x=60,
                    y=270,
                    label="Midpoint Formula"
                ),
                TextCommand(
                    id="discard_label",
                    content="Discarded elements: 2, 5, 8, 12, 16 (since 23 > 16)",
                    x=60,
                    y=330,
                    size=16,
                    color="#dc2626"
                )
            ],
            code_action=CodeAction(
                code=(
                    "# Calculating midpoint in Python\n"
                    "low = 0\n"
                    "high = 9\n"
                    "mid = (low + high) // 2\n"
                    "print(f'low: {low}, high: {high} -> mid index: {mid}')\n"
                ),
                language="python",
                action="execute",
                explanation="Integer division (//) safely computes the floor of the midpoint."
            ),
            tool_calls=[
                execute_tool_call("draw_on_board", {"commands": ["box_highlight", "arr_mid", "eq_mid"]}),
                execute_tool_call("run_code", {"code": "mid = (low + high) // 2", "language": "python"})
            ],
            is_final_step=False
        ),

        # Step 2: Formative Checkpoint Question
        LessonStep(
            step_id="bs_step_2",
            step_index=2,
            total_steps=5,
            concept="Binary Search",
            narration=(
                "Let's make sure we have this down before writing the full loop. "
                "Since our target is 23 and array[mid] is 16 (so target > array[mid]), "
                "how must we update our search bounds for the next round?"
            ),
            agent_thoughts="Checking if student understands adjusting the lower bound: low = mid + 1.",
            board_commands=[
                TextCommand(
                    id="checkpoint_title",
                    content="Checkpoint: Updating Search Bounds",
                    x=60,
                    y=50,
                    size=22,
                    color="#1e293b"
                ),
                TextCommand(
                    id="checkpoint_rule",
                    content="Rule: If target > array[mid], target is in the right half.",
                    x=60,
                    y=100,
                    size=16,
                    color="#2563eb"
                ),
                EquationCommand(
                    id="eq_rule",
                    latex=r"\text{target} > \text{array}[mid] \implies low = mid + 1",
                    x=60,
                    y=150,
                    label="Bound Update Formula"
                )
            ],
            check_question=CheckQuestion(
                question_id="bs_check_bounds",
                question="When target (23) is greater than array[mid] (16), what is the correct update?",
                options=[
                    "high = mid - 1",
                    "low = mid + 1",
                    "low = mid",
                    "high = mid"
                ],
                correct_index=1,
                explanation="Because array[mid] was already checked and is too small, we set low = mid + 1 to inspect only elements to its right.",
                concept_tag="binary_search_bounds_update"
            ),
            tool_calls=[
                execute_tool_call("ask_check_question", {
                    "question_id": "bs_check_bounds",
                    "question": "When target (23) is greater than array[mid] (16), what is the correct update?",
                    "options": ["high = mid - 1", "low = mid + 1", "low = mid", "high = mid"],
                    "correct_index": 1,
                    "explanation": "We set low = mid + 1.",
                    "concept_tag": "binary_search_bounds_update"
                })
            ],
            is_final_step=False
        ),

        # Step 3: Live Code Implementation & Execution
        LessonStep(
            step_id="bs_step_3",
            step_index=3,
            total_steps=5,
            concept="Binary Search",
            narration=(
                "Spot on! Now let's assemble the complete Python algorithm. "
                "Notice our loop condition: while low <= high. "
                "Inside, we compute mid, check for match, and shift low or high. "
                "Let's run the code live in our browser Python runtime to see every step printed out!"
            ),
            agent_thoughts="Live coding step. Monaco editor populated with binary_search and executed via Pyodide.",
            board_commands=[
                TextCommand(
                    id="algo_title",
                    content="Full Binary Search Algorithm",
                    x=60,
                    y=50,
                    size=22,
                    color="#0f172a"
                ),
                EquationCommand(
                    id="eq_recurrence",
                    latex=r"T(n) = T\left(\frac{n}{2}\right) + \mathcal{O}(1) = \mathcal{O}(\log n)",
                    x=60,
                    y=110,
                    label="Recurrence Relation"
                ),
                MermaidCommand(
                    id="chart_steps",
                    chart="graph TD\n  Start[low=0, high=9] --> Step1[mid=4, val=16 < 23]\n  Step1 --> Step2[low=5, high=9, mid=7, val=56 > 23]\n  Step2 --> Step3[low=5, high=6, mid=5, val=23 == 23]\n  Step3 --> Found[Target Found at Index 5!]",
                    x=60,
                    y=180,
                    title="Execution Path for Target 23"
                )
            ],
            code_action=CodeAction(
                code=(
                    "def binary_search(arr, target):\n"
                    "    low = 0\n"
                    "    high = len(arr) - 1\n"
                    "    \n"
                    "    while low <= high:\n"
                    "        mid = (low + high) // 2\n"
                    "        val = arr[mid]\n"
                    "        print(f'Checking range [{low}..{high}], mid={mid}, val={val}')\n"
                    "        \n"
                    "        if val == target:\n"
                    "            return mid\n"
                    "        elif val < target:\n"
                    "            low = mid + 1\n"
                    "        else:\n"
                    "            high = mid - 1\n"
                    "            \n"
                    "    return -1\n\n"
                    "# Demo run\n"
                    "numbers = [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]\n"
                    "target = 23\n"
                    "idx = binary_search(numbers, target)\n"
                    "print(f'Target {target} located at index: {idx}')\n"
                ),
                language="python",
                action="execute",
                explanation="Iterative Binary Search with time complexity O(log n) and space complexity O(1)."
            ),
            tool_calls=[
                execute_tool_call("draw_on_board", {"commands": ["algo_title", "eq_recurrence", "chart_steps"]}),
                execute_tool_call("run_code", {"code": "def binary_search...", "language": "python"})
            ],
            is_final_step=False
        ),

        # Step 4: Mastery Update & Recommendation
        LessonStep(
            step_id="bs_step_4",
            step_index=4,
            total_steps=5,
            concept="Binary Search",
            narration=(
                "Fantastic progress! You've learned how Binary Search divides the search space in half, "
                "how to update the search bounds, and how to implement the loop in Python. "
                "I've updated your mastery score for 'binary_search_basics' to 85%. "
                "Next up: handling duplicate elements and edge cases like integer overflow in other languages."
            ),
            agent_thoughts="Concluding lesson. Calling update_mastery tool and recommend_next tool.",
            board_commands=[
                ClearCommand(id="clear_end"),
                TextCommand(
                    id="finish_title",
                    content="Lesson Complete: Binary Search Mastery",
                    x=60,
                    y=50,
                    size=24,
                    color="#16a34a"
                ),
                BoxCommand(
                    id="badge_box",
                    label="Binary Search Mastered (+0.35)",
                    x=60,
                    y=110,
                    width=280,
                    height=60,
                    color="#16a34a",
                    fill="#f0fdf4"
                ),
                TextCommand(
                    id="recommend_text",
                    content="Next recommended practice: Binary Search on Rotated Sorted Arrays",
                    x=60,
                    y=200,
                    size=18,
                    color="#1e293b"
                ),
                MermaidCommand(
                    id="roadmap",
                    chart="graph LR\n  A[Binary Search Basics (Done)] --> B[Duplicate Elements]\n  B --> C[Rotated Arrays]\n  C --> D[Binary Search on Answer Range]",
                    x=60,
                    y=260,
                    title="Mastery Roadmap"
                )
            ],
            tool_calls=[
                execute_tool_call("update_mastery", {
                    "student_id": "demo_student",
                    "concept": "binary_search_basics",
                    "score_delta": 0.35
                }),
                execute_tool_call("recommend_next", {
                    "student_id": "demo_student",
                    "weak_concepts": ["binary_search_duplicates", "rotated_array_search"]
                })
            ],
            is_final_step=True
        )
    ]
    return steps


class TeacherAgent:
    def __init__(self):
        self.mock_steps = get_mock_binary_search_steps()

    async def get_next_step(self, req: LessonStepRequest) -> LessonStep:
        idx = max(0, min(req.step_index, len(self.mock_steps) - 1))

        # If student provided feedback like "I don't understand", customize the explanation
        if req.feedback and "understand" in req.feedback.lower():
            base_step = self.mock_steps[idx]
            adapted_narration = (
                f"No worries, let me break this down even simpler! "
                f"Instead of thinking about code, imagine you have a list of sorted numbers. "
                f"Every time we look at the middle number, we instantly cross out half of the list. "
                f"{base_step.narration}"
            )
            return LessonStep(
                step_id=f"{base_step.step_id}_adapted",
                step_index=base_step.step_index,
                total_steps=base_step.total_steps,
                concept=base_step.concept,
                narration=adapted_narration,
                agent_thoughts="Student expressed confusion: decomposing step into simpler physical intuition.",
                board_commands=base_step.board_commands,
                code_action=base_step.code_action,
                check_question=base_step.check_question,
                tool_calls=base_step.tool_calls,
                is_final_step=base_step.is_final_step,
            )

        # Fallback factory for LLM router
        def fallback():
            return self.mock_steps[idx]

        prompt = (
            f"You are an encouraging, expert AI virtual teacher.\n"
            f"Topic: {req.concept}\n"
            f"Step requested: {req.step_index} of {len(self.mock_steps)}\n"
            f"Learner ID: {req.student_id}\n"
            f"Previous response: {req.last_student_response}\n"
            f"Student misconceptions: {req.student_misconceptions}\n"
            f"Generate a structured LessonStep with narration, whiteboard commands (text, box, arrow, equation, mermaid), "
            f"optional code_action for live coding, optional check_question, agent_thoughts, and tool_calls."
        )

        return await router.generate_structured(
            prompt=prompt,
            response_model=LessonStep,
            mock_fallback_factory=fallback
        )

    async def handle_chat(self, req: ChatMessageRequest) -> ChatMessageResponse:
        """Handle ad-hoc student question during the lesson."""
        def fallback():
            return ChatMessageResponse(
                reply=(
                    f"Great question about {req.concept}! Remember that Binary Search requires the array to be sorted first. "
                    f"If the array is unsorted, we cannot know which half contains the target without checking every element."
                ),
                agent_thoughts="Explaining sorting precondition for binary search.",
                suggested_board_commands=[
                    TextCommand(
                        id="chat_note",
                        content="Key Rule: Binary Search requires sorted input!",
                        x=60,
                        y=380,
                        size=16,
                        color="#b91c1c"
                    )
                ]
            )

        prompt = (
            f"The student asks during step {req.current_step_index} of {req.concept}: '{req.message}'\n"
            f"Provide a clear, brief pedagogical reply and optional whiteboard board commands to clarify."
        )

        return await router.generate_structured(
            prompt=prompt,
            response_model=ChatMessageResponse,
            mock_fallback_factory=fallback
        )


teacher_agent = TeacherAgent()
