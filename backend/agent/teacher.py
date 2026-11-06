import json
import logging
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
    CheckAnswerRequest,
    CheckAnswerResponse,
    ToolCallRecord,
    AttemptRecordRequest,
    AgentTrace,
)
from backend.agent.llm_router import router
from backend.agent.tools import execute_tool_call
from backend.agent.client import learner_client

logger = logging.getLogger("teacher_agent")


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
                BoxCommand(id="box_0", label="2", x=60, y=130, width=55, height=50, color="#cbd5e1", fill="#f1f5f9"),
                BoxCommand(id="box_1", label="5", x=125, y=130, width=55, height=50, color="#cbd5e1", fill="#f1f5f9"),
                BoxCommand(id="box_2", label="8", x=190, y=130, width=55, height=50, color="#cbd5e1", fill="#f1f5f9"),
                BoxCommand(id="box_3", label="12", x=255, y=130, width=55, height=50, color="#cbd5e1", fill="#f1f5f9"),
                BoxCommand(id="box_4", label="16", x=320, y=130, width=55, height=50, color="#d97706", fill="#fef3c7"),
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


def get_mock_recursion_steps() -> List[LessonStep]:
    """Generates the second canned 5-step interactive lesson on Recursion."""
    steps = [
        # Step 0: Intuition & Self-Similarity
        LessonStep(
            step_id="rec_step_0",
            step_index=0,
            total_steps=5,
            concept="Recursion",
            narration=(
                "Welcome to Recursion! Recursion is the art of solving a computational problem "
                "by having a function call itself on a strictly smaller subproblem. "
                "Think of Russian nesting dolls (Matryoshka): every doll contains an identical, "
                "smaller doll inside, until you finally reach the solid, indivisible core—the Base Case!"
            ),
            agent_thoughts="Goal: Introduce recursion intuition using Russian dolls and factorial call-chain diagram.",
            board_commands=[
                ClearCommand(id="clear_rec_0"),
                TextCommand(
                    id="rec_title",
                    content="Recursion: Self-Similarity & Delegation",
                    x=60,
                    y=40,
                    size=24,
                    color="#0f172a"
                ),
                TextCommand(
                    id="rec_math_label",
                    content="Mathematical Definition: Factorial Function",
                    x=60,
                    y=80,
                    size=16,
                    color="#475569"
                ),
                EquationCommand(
                    id="rec_eq_1",
                    latex=r"n! = \begin{cases} 1 & \text{if } n \le 1 \quad \text{(Base Case)} \\ n \times (n-1)! & \text{if } n > 1 \quad \text{(Recursive Step)} \end{cases}",
                    x=60,
                    y=110,
                    color="#0284c7"
                ),
                MermaidCommand(
                    id="rec_chain_chart",
                    chart="graph TD\n  F4[\"factorial(4)\"] --> F3[\"factorial(3)\"]\n  F3 --> F2[\"factorial(2)\"]\n  F2 --> F1[\"factorial(1) (BASE CASE returns 1)\"]",
                    x=60,
                    y=200,
                    title="Call Chain: Winding Down to Base Case"
                )
            ],
            code_action=CodeAction(
                code=(
                    "def factorial(n: int) -> int:\n"
                    "    # Base case: stop the recursive descent\n"
                    "    if n <= 1:\n"
                    "        return 1\n"
                    "    # Recursive case: self-delegation\n"
                    "    return n * factorial(n - 1)\n\n"
                    "print('4! =', factorial(4))  # Output: 24\n"
                ),
                language="python",
                explanation="Notice how factorial(4) halts only when factorial(1) hits the base case and returns 1."
            ),
            tool_calls=[
                execute_tool_call("draw_on_board", {"element": "recursion_call_chain", "concept": "recursion_intuition"}),
                execute_tool_call("run_code", {"language": "python", "snippet": "factorial(4)"})
            ]
        ),
        # Step 1: The Base Case Requirement
        LessonStep(
            step_id="rec_step_1",
            step_index=1,
            total_steps=5,
            concept="Recursion",
            narration=(
                "The most critical rule in recursive design is the Base Case. "
                "Every recursive path MUST have at least one condition that returns directly without a self-call. "
                "Without a base case, or if the parameter doesn't converge toward it, "
                "calls pile up indefinitely until Python raises RecursionError: maximum recursion depth exceeded!"
            ),
            agent_thoughts="Goal: Emphasize the mandatory base case to prevent stack overflow errors.",
            board_commands=[
                TextCommand(
                    id="rec_base_title",
                    content="The Golden Rule: Mandatory Terminating Base Case",
                    x=60,
                    y=40,
                    size=22,
                    color="#0f172a"
                ),
                BoxCommand(
                    id="base_case_highlight",
                    x=50,
                    y=85,
                    width=680,
                    height=90,
                    color="#dc2626",
                    fill="#fef2f2"
                ),
                TextCommand(
                    id="base_case_warning",
                    content="WARNING: if n <= 1: return 1\nMissing this condition creates infinite recursion and crashes!",
                    x=70,
                    y=110,
                    size=16,
                    color="#991b1b"
                ),
                EquationCommand(
                    id="rec_depth_eq",
                    latex=r"\lim_{k \to \infty} \text{StackDepth}(k) \implies \text{RecursionError: Stack Overflow}",
                    x=60,
                    y=200,
                    color="#dc2626"
                )
            ],
            check_question=CheckQuestion(
                question_id="rec_check_base_case",
                concept_tag="recursion_base_case",
                question="What happens in Python if a recursive function fails to define or reach a valid base case?",
                options=[
                    "The function quietly returns None",
                    "A RecursionError / Stack Overflow occurs when memory limit is exceeded",
                    "Python automatically transforms it into an iterative while loop",
                    "The interpreter applies tail-call optimization automatically"
                ],
                correct_index=1,
                explanation="Without a reachable base case, stack frames consume all allocated call stack memory, triggering a RecursionError."
            ),
            tool_calls=[
                execute_tool_call("ask_check_question", {
                    "question_id": "rec_check_base_case",
                    "concept": "recursion_base_case"
                })
            ]
        ),
        # Step 2: The Call Stack & LIFO Unwinding
        LessonStep(
            step_id="rec_step_2",
            step_index=2,
            total_steps=5,
            concept="Recursion",
            narration=(
                "How does the computer remember where to return? The Call Stack! "
                "Each active call allocates an activation record (frame) holding parameters and local state. "
                "Because the stack is Last-In, First-Out (LIFO), the deepest call completes first, "
                "then unwinds backwards: factorial(1) -> factorial(2) -> factorial(3) -> factorial(4) = 24!"
            ),
            agent_thoughts="Goal: Demystify the return phase via LIFO stack unwinding visualization.",
            board_commands=[
                ClearCommand(id="clear_rec_2"),
                TextCommand(
                    id="stack_title",
                    content="The Call Stack: Last-In, First-Out (LIFO) Unwinding",
                    x=60,
                    y=40,
                    size=22,
                    color="#0f172a"
                ),
                MermaidCommand(
                    id="unwind_stack_chart",
                    chart="graph BT\n  F1[\"factorial(1) = 1 (Bottom resolves first)\"] --> F2[\"factorial(2) = 2 * 1 = 2\"]\n  F2 --> F3[\"factorial(3) = 3 * 2 = 6\"]\n  F3 --> F4[\"factorial(4) = 4 * 6 = 24 (Top resolves last)\"]",
                    x=60,
                    y=90,
                    title="Stack Unwinding Order (LIFO Return Phase)"
                ),
                EquationCommand(
                    id="rec_time_eq",
                    latex=r"T(n) = T(n-1) + O(1) = O(n) \text{ time}, \quad S(n) = O(n) \text{ auxiliary call stack space}",
                    x=60,
                    y=260,
                    color="#047857"
                )
            ],
            check_question=CheckQuestion(
                question_id="rec_check_call_stack",
                concept_tag="recursion_call_stack",
                question="In what order do suspended recursive stack frames resolve their return values?",
                options=[
                    "First-In, First-Out (FIFO)",
                    "Last-In, First-Out (LIFO)",
                    "Random non-deterministic order",
                    "Simultaneously across CPU threads"
                ],
                correct_index=1,
                explanation="Function calls push onto a call stack (LIFO structure); the most recent frame completes and pops first."
            ),
            tool_calls=[
                execute_tool_call("ask_check_question", {
                    "question_id": "rec_check_call_stack",
                    "concept": "recursion_call_stack"
                })
            ]
        ),
        # Step 3: Branching Tree Traversal
        LessonStep(
            step_id="rec_step_3",
            step_index=3,
            total_steps=5,
            concept="Recursion",
            narration=(
                "Recursion truly shines when dealing with branching structures like trees and graphs. "
                "In a Binary Search Tree (BST), an In-Order traversal simply says: "
                "traverse(left), process(node), traverse(right). "
                "Three lines of recursive code do what would require a complex explicit stack in iteration!"
            ),
            agent_thoughts="Goal: Show why recursion is natural for trees via in-order traversal.",
            board_commands=[
                ClearCommand(id="clear_rec_3"),
                TextCommand(
                    id="tree_title",
                    content="Branching Recursion: Binary Tree Traversal",
                    x=60,
                    y=40,
                    size=22,
                    color="#0f172a"
                ),
                MermaidCommand(
                    id="tree_diagram",
                    chart="graph TD\n  4[\"4 (Root)\"] --> 2[\"2 (Left)\"]\n  4 --> 6[\"6 (Right)\"]\n  2 --> 1[\"1 (Left)\"]\n  2 --> 3[\"3 (Right)\"]\n  6 --> 5[\"5 (Left)\"]\n  6 --> 7[\"7 (Right)\"]",
                    x=60,
                    y=80,
                    title="Binary Search Tree Structure"
                )
            ],
            code_action=CodeAction(
                code=(
                    "class TreeNode:\n"
                    "    def __init__(self, val=0, left=None, right=None):\n"
                    "        self.val = val\n"
                    "        self.left = left\n"
                    "        self.right = right\n\n"
                    "def inorder_traversal(root: TreeNode) -> list:\n"
                    "    if not root:  # Base case: empty leaf\n"
                    "        return []\n"
                    "    # Left Subtree + Root + Right Subtree\n"
                    "    return inorder_traversal(root.left) + [root.val] + inorder_traversal(root.right)\n\n"
                    "# Builds sorted order: [1, 2, 3, 4, 5, 6, 7]\n"
                ),
                language="python",
                explanation="In-order recursive traversal visits the left branch, records the value, then visits the right branch."
            ),
            tool_calls=[
                execute_tool_call("run_code", {"language": "python", "snippet": "inorder_traversal(tree_root)"})
            ]
        ),
        # Step 4: Recursion vs Iteration & Mastery Wrap-up
        LessonStep(
            step_id="rec_step_4",
            step_index=4,
            total_steps=5,
            concept="Recursion",
            narration=(
                "Mastering recursion means knowing when to use it! "
                "Recursion is elegant and intuitive for hierarchical data (trees, graphs, divide-and-conquer). "
                "However, each call costs memory on the stack: O(h) space where h is maximum recursion depth. "
                "Congratulations! You now understand Base Cases, Call Stacks, and Tree Traversal!"
            ),
            agent_thoughts="Goal: Synthesize tradeoffs between recursion and iteration, update student mastery.",
            board_commands=[
                ClearCommand(id="clear_rec_4"),
                TextCommand(
                    id="summary_title",
                    content="Recursion Mastery: Tradeoffs & Space Complexity",
                    x=60,
                    y=40,
                    size=22,
                    color="#0f172a"
                ),
                BoxCommand(
                    id="summary_box",
                    x=50,
                    y=80,
                    width=680,
                    height=130,
                    color="#16a34a",
                    fill="#f0fdf4"
                ),
                TextCommand(
                    id="summary_checklist",
                    content=(
                        "✓ Base Case: Halts recursive descent, prevents stack overflow\n"
                        "✓ Call Stack (LIFO): Suspends frames and unwinds from deepest call\n"
                        "✓ Auxiliary Space: O(h) stack depth memory overhead\n"
                        "✓ Ideal Applications: Trees, Divide-and-Conquer, Graph DFS"
                    ),
                    x=70,
                    y=105,
                    size=15,
                    color="#14532d"
                ),
                EquationCommand(
                    id="rec_space_eq",
                    latex=r"\text{Call Stack Overhead} = O(\text{max depth } h) \quad \text{vs Iteration } O(1)",
                    x=60,
                    y=230,
                    color="#0284c7"
                )
            ],
            check_question=CheckQuestion(
                question_id="rec_check_complexity",
                concept_tag="recursion_space_complexity",
                question="What is the primary auxiliary memory cost of recursion compared to iteration?",
                options=[
                    "Zero memory overhead",
                    "O(h) call stack memory where h is maximum recursion depth",
                    "O(2^n) exponential heap memory always",
                    "CPU register spills"
                ],
                correct_index=1,
                explanation="Each pending recursive invocation retains an activation frame on the call stack until returned, costing O(depth) memory."
            ),
            tool_calls=[
                execute_tool_call("update_mastery", {
                    "student_id": "demo_student",
                    "concept": "recursion_fundamentals",
                    "score_delta": 0.35
                }),
                execute_tool_call("recommend_next", {
                    "student_id": "demo_student",
                    "weak_concepts": ["recursion_memoization", "tail_recursion"]
                })
            ],
            is_final_step=True
        )
    ]
    return steps


class TeacherAgent:
    def __init__(self):
        self.mock_bs_steps = get_mock_binary_search_steps()
        self.mock_rec_steps = get_mock_recursion_steps()
        self.mock_steps = self.mock_bs_steps

    def evaluate_check_answer(self, req: CheckAnswerRequest) -> CheckAnswerResponse:
        """
        Evaluate checkpoint answer, diagnose misconceptions, update learner model,
        and generate corrective remediation.
        """
        # Question bs_check_bounds: correct index is 1 (low = mid + 1)
        is_corr = (req.selected_index == 1)

        if is_corr:
            learner_client.record_attempt(AttemptRecordRequest(
                user_id=req.student_id,
                concept_tag="binary_search_bounds_update",
                is_correct=True,
                question_id=req.question_id
            ))
            return CheckAnswerResponse(
                is_correct=True,
                correct_index=1,
                explanation="Correct! Because array[mid] is smaller than our target, the target must lie strictly to the right, so low = mid + 1.",
                detected_misconception=None,
                remediation=None,
                updated_mastery_score=0.85,
                suggested_board_commands=[
                    TextCommand(
                        id="correct_badge",
                        content="Correct: low = mid + 1 selected!",
                        x=60,
                        y=350,
                        size=18,
                        color="#16a34a"
                    )
                ],
                trace=AgentTrace(
                    source="fallback_canned",
                    provider="internal",
                    model="rule_taxonomy",
                    latency_ms=2,
                    detected_misconception=None,
                    strategy_chosen="positive_reinforcement",
                    mastery_before=0.80,
                    mastery_after=0.85,
                    provider_used="internal"
                )
            )

        # Misconception taxonomy for checkpoint question
        misconception_map = {
            0: (
                "confuses_direction_when_target_greater",
                "You selected 'high = mid - 1'. This shrinks the right bound, but because target (23) > array[mid] (16), the target is to the RIGHT. You must advance 'low = mid + 1' instead."
            ),
            2: (
                "fails_to_exclude_checked_midpoint",
                "You selected 'low = mid'. We have already checked array[mid] and confirmed it is NOT the target. You must advance past it to 'low = mid + 1' to avoid an infinite loop."
            ),
            3: (
                "confuses_bounds_and_fails_exclusion",
                "You selected 'high = mid'. Setting high = mid searches the left half and fails to exclude mid. The correct update is low = mid + 1."
            )
        }
        mis_tag, remediation_msg = misconception_map.get(
            req.selected_index,
            ("confuses_boundary_adjustment", "Incorrect bound update. If target > array[mid], advance low = mid + 1.")
        )

        # Update learner model with failed attempt and misconception tag
        att = learner_client.record_attempt(AttemptRecordRequest(
            user_id=req.student_id,
            concept_tag="binary_search_bounds_update",
            is_correct=False,
            misconceptions=[mis_tag],
            question_id=req.question_id
        ))

        return CheckAnswerResponse(
            is_correct=False,
            correct_index=1,
            explanation="When target > array[mid], target is in the right half: low = mid + 1.",
            detected_misconception=mis_tag,
            remediation=remediation_msg,
            updated_mastery_score=att.new_mastery_score,
            suggested_board_commands=[
                TextCommand(
                    id="misconception_alert",
                    content=f"Diagnosed Misconception: {mis_tag}",
                    x=60,
                    y=350,
                    size=16,
                    color="#dc2626"
                ),
                TextCommand(
                    id="remediation_note",
                    content=remediation_msg,
                    x=60,
                    y=385,
                    size=14,
                    color="#b91c1c"
                )
            ],
            trace=AgentTrace(
                source="fallback_canned",
                provider="internal",
                model="rule_taxonomy",
                latency_ms=5,
                detected_misconception=mis_tag,
                strategy_chosen="visual_remediation",
                mastery_before=0.55,
                mastery_after=att.new_mastery_score,
                provider_used="internal"
            )
        )

    async def get_next_step(self, req: LessonStepRequest) -> LessonStep:
        active_steps = self.mock_rec_steps if "recursion" in req.concept.lower() else self.mock_bs_steps
        idx = max(0, min(req.step_index, len(active_steps) - 1))

        # Check if student answered a previous checkpoint incorrectly
        if req.last_student_response is not None:
            ans = str(req.last_student_response).strip()
            # If answer is wrong (not '1' or 'low = mid + 1')
            if ans not in ("1", "low = mid + 1", "correct"):
                eval_res = self.evaluate_check_answer(CheckAnswerRequest(
                    question_id="bs_check_bounds",
                    selected_index=int(ans) if ans.isdigit() else 0,
                    concept=req.concept,
                    student_id=req.student_id
                ))
                # Return an adaptive remediation teaching step
                base_step = active_steps[idx]
                return LessonStep(
                    step_id=f"{base_step.step_id}_remediation",
                    step_index=base_step.step_index,
                    total_steps=base_step.total_steps,
                    concept=base_step.concept,
                    narration=(
                        f"I noticed you selected an update that doesn't match the search direction. "
                        f"{eval_res.remediation} Let's look at the board again: since our target 23 is larger "
                        f"than 16, everything at index 4 and below is discarded. We set low = 4 + 1 = 5."
                    ),
                    agent_thoughts=f"Student selected option '{ans}'. Diagnosed misconception: {eval_res.detected_misconception}. Providing corrective visual remediation.",
                    detected_misconception=eval_res.detected_misconception,
                    remediation=eval_res.remediation,
                    board_commands=base_step.board_commands + eval_res.suggested_board_commands,
                    code_action=base_step.code_action,
                    check_question=base_step.check_question,
                    tool_calls=[
                        execute_tool_call("update_mastery", {
                            "student_id": req.student_id,
                            "concept": "binary_search_bounds_update",
                            "score_delta": -0.10,
                            "is_correct": False,
                            "misconceptions": [eval_res.detected_misconception]
                        })
                    ],
                    is_final_step=base_step.is_final_step,
                    trace=AgentTrace(
                        detected_misconception=eval_res.detected_misconception,
                        strategy_chosen="visual_remediation",
                        mastery_before=0.55,
                        mastery_after=eval_res.updated_mastery_score,
                        provider_used="mock"
                    ),
                )

        # If student provided "I don't understand" feedback
        if req.feedback and "understand" in req.feedback.lower():
            base_step = self.mock_steps[idx]
            adapted_narration = (
                f"No worries, let me break this down even simpler! "
                f"Instead of thinking about formulas, imagine a dictionary. "
                f"When looking for a word starting with 'M', opening to 'D' tells you immediately "
                f"that all pages before 'D' are useless. "
                f"{base_step.narration}"
            )
            return LessonStep(
                step_id=f"{base_step.step_id}_adapted",
                step_index=base_step.step_index,
                total_steps=base_step.total_steps,
                concept=base_step.concept,
                narration=adapted_narration,
                agent_thoughts="Student expressed confusion: decomposing step into simpler physical dictionary intuition.",
                detected_misconception="general_conceptual_confusion",
                remediation="Simplified conceptual analogy provided.",
                board_commands=base_step.board_commands,
                code_action=base_step.code_action,
                check_question=base_step.check_question,
                tool_calls=base_step.tool_calls,
                is_final_step=base_step.is_final_step,
                trace=AgentTrace(
                    detected_misconception="general_conceptual_confusion",
                    strategy_chosen="physical_analogy_simplification",
                    mastery_before=0.50,
                    mastery_after=0.50,
                    provider_used="mock"
                ),
            )

        # Fallback factory for LLM router
        def fallback():
            return active_steps[idx]

        # Fetch learner mastery profile to personalize prompt
        mastery_profile = learner_client.get_mastery(req.student_id)
        weak_data = learner_client.get_weak_concepts(req.student_id)
        weak_list = [w.concept_tag for w in weak_data.weak_concepts]

        prompt = (
            f"You are an expert, encouraging AI virtual teacher.\n"
            f"Teaching Topic: {req.concept}\n"
            f"Step requested: {req.step_index} of {len(self.mock_steps)}\n"
            f"Learner ID: {req.student_id}\n"
            f"Current Mastery Profile: {mastery_profile.concept_scores}\n"
            f"Weak Concepts: {weak_list}\n"
            f"Student misconceptions: {req.student_misconceptions}\n\n"
            f"Generate a structured LessonStep object adhering strictly to the JSON schema:\n"
            f"- step_id, step_index ({req.step_index}), total_steps (5), concept ('{req.concept}')\n"
            f"- narration: spoken explanation\n"
            f"- board_commands: list of whiteboard commands (text, box, arrow, equation, mermaid)\n"
            f"- optional code_action (python snippet)\n"
            f"- optional check_question (4 options, correct_index, explanation, concept_tag)\n"
            f"- agent_thoughts (visible reasoning)\n"
            f"- tool_calls: list of tool calls made (e.g. draw_on_board, ask_check_question)\n"
            f"- is_final_step: {req.step_index == 4}"
        )

        res = router.generate_structured_sync(
            prompt=prompt,
            response_model=LessonStep,
            mock_fallback_factory=fallback
        )
        if res.trace is None:
            c_tag = req.concept.lower().replace(" ", "_")
            current_m = mastery_profile.concept_scores.get(c_tag, 0.5)
            res.trace = AgentTrace(
                detected_misconception=res.detected_misconception,
                strategy_chosen="direct_instruction",
                mastery_before=current_m,
                mastery_after=current_m,
                provider_used=(res.provider_metadata or {}).get("provider", "mock")
            )
        return res

    def get_next_step_sync(self, req: LessonStepRequest) -> LessonStep:
        active_steps = self.mock_rec_steps if "recursion" in req.concept.lower() else self.mock_bs_steps
        idx = max(0, min(req.step_index, len(active_steps) - 1))

        # Check if student answered a previous checkpoint incorrectly
        if req.last_student_response is not None:
            ans = str(req.last_student_response).strip()
            # If answer is wrong (not '1' or 'low = mid + 1')
            if ans not in ("1", "low = mid + 1", "correct"):
                eval_res = self.evaluate_check_answer(CheckAnswerRequest(
                    question_id="bs_check_bounds",
                    selected_index=int(ans) if ans.isdigit() else 0,
                    concept=req.concept,
                    student_id=req.student_id
                ))
                base_step = active_steps[idx]
                return LessonStep(
                    step_id=f"{base_step.step_id}_remediation",
                    step_index=base_step.step_index,
                    total_steps=base_step.total_steps,
                    concept=base_step.concept,
                    narration=(
                        f"I noticed you selected an update that doesn't match the search direction. "
                        f"{eval_res.remediation} Let's look at the board again: since our target 23 is larger "
                        f"than 16, everything at index 4 and below is discarded. We set low = 4 + 1 = 5."
                    ),
                    agent_thoughts=f"Student selected option '{ans}'. Diagnosed misconception: {eval_res.detected_misconception}. Providing corrective visual remediation.",
                    detected_misconception=eval_res.detected_misconception,
                    remediation=eval_res.remediation,
                    board_commands=base_step.board_commands + eval_res.suggested_board_commands,
                    code_action=base_step.code_action,
                    check_question=base_step.check_question,
                    tool_calls=[
                        execute_tool_call("update_mastery", {
                            "student_id": req.student_id,
                            "concept": "binary_search_bounds_update",
                            "score_delta": -0.10,
                            "is_correct": False,
                            "misconceptions": [eval_res.detected_misconception]
                        })
                    ],
                    is_final_step=base_step.is_final_step,
                    trace=AgentTrace(
                        source="fallback_canned",
                        provider="internal",
                        model="rule_remediation",
                        latency_ms=10,
                        detected_misconception=eval_res.detected_misconception,
                        strategy_chosen="visual_remediation",
                        mastery_before=0.55,
                        mastery_after=eval_res.updated_mastery_score,
                        provider_used="internal"
                    ),
                )

        # If student provided "I don't understand" feedback
        if req.feedback and "understand" in req.feedback.lower():
            base_step = self.mock_steps[idx]
            adapted_narration = (
                f"No worries, let me break this down even simpler! "
                f"Instead of thinking about formulas, imagine a dictionary. "
                f"When looking for a word starting with 'M', opening to 'D' tells you immediately "
                f"that all pages before 'D' are useless. "
                f"{base_step.narration}"
            )
            return LessonStep(
                step_id=f"{base_step.step_id}_adapted",
                step_index=base_step.step_index,
                total_steps=base_step.total_steps,
                concept=base_step.concept,
                narration=adapted_narration,
                agent_thoughts="Student expressed confusion: decomposing step into simpler physical dictionary intuition.",
                detected_misconception="general_conceptual_confusion",
                remediation="Simplified conceptual analogy provided.",
                board_commands=base_step.board_commands,
                code_action=base_step.code_action,
                check_question=base_step.check_question,
                tool_calls=base_step.tool_calls,
                is_final_step=base_step.is_final_step,
                trace=AgentTrace(
                    source="fallback_canned",
                    provider="internal",
                    model="socratic_analogy",
                    latency_ms=5,
                    detected_misconception="general_conceptual_confusion",
                    strategy_chosen="physical_analogy_simplification",
                    mastery_before=0.50,
                    mastery_after=0.50,
                    provider_used="internal"
                ),
            )

        def fallback():
            return active_steps[idx]

        mastery_profile = learner_client.get_mastery(req.student_id)
        weak_data = learner_client.get_weak_concepts(req.student_id)
        weak_list = [w.concept_tag for w in weak_data.weak_concepts]

        prompt = (
            f"You are an expert, encouraging AI virtual teacher.\n"
            f"Teaching Topic: {req.concept}\n"
            f"Step requested: {req.step_index} of {len(self.mock_steps)}\n"
            f"Learner ID: {req.student_id}\n"
            f"Current Mastery Profile: {mastery_profile.concept_scores}\n"
            f"Weak Concepts: {weak_list}\n"
            f"Student misconceptions: {req.student_misconceptions}\n\n"
            f"Generate a structured LessonStep object adhering strictly to the JSON schema:\n"
            f"- step_id, step_index ({req.step_index}), total_steps (5), concept ('{req.concept}')\n"
            f"- narration: spoken explanation\n"
            f"- board_commands: list of whiteboard commands (text, box, arrow, equation, mermaid)\n"
            f"- optional code_action (python snippet)\n"
            f"- optional check_question (4 options, correct_index, explanation, concept_tag)\n"
            f"- agent_thoughts (visible reasoning)\n"
            f"- tool_calls: list of tool calls made (e.g. draw_on_board, ask_check_question)\n"
            f"- is_final_step: {req.step_index == 4}"
        )

        res = router.generate_structured_sync(
            prompt=prompt,
            response_model=LessonStep,
            mock_fallback_factory=fallback
        )
        if res.step_id != active_steps[idx].step_id:
            return active_steps[idx].model_copy(update={
                "trace": AgentTrace(
                    source=res.trace.source if res.trace else "fallback_canned",
                    provider=res.trace.provider if res.trace else "internal",
                    model="canned_lesson",
                    latency_ms=0,
                    strategy_chosen="direct_instruction",
                    provider_used=res.trace.provider_used if res.trace else "internal",
                )
            })
        c_tag = req.concept.lower().replace(" ", "_")
        current_m = mastery_profile.concept_scores.get(c_tag, 0.5)
        if res.trace is None:
            res.trace = AgentTrace(
                source="mock",
                provider="mock",
                model="canned",
                latency_ms=0,
                detected_misconception=res.detected_misconception,
                strategy_chosen="direct_instruction",
                mastery_before=current_m,
                mastery_after=current_m,
                provider_used="mock"
            )
        else:
            res.trace.detected_misconception = res.trace.detected_misconception or res.detected_misconception
            if res.trace.source == "cache":
                res.trace.strategy_chosen = "direct_instruction"
            else:
                res.trace.strategy_chosen = res.trace.strategy_chosen or "direct_instruction"
            if res.trace.mastery_before is None:
                res.trace.mastery_before = current_m
            if res.trace.mastery_after is None:
                res.trace.mastery_after = current_m
        return res

    async def get_next_step(self, req: LessonStepRequest) -> LessonStep:
        return self.get_next_step_sync(req)

    def handle_chat_sync(self, req: ChatMessageRequest) -> ChatMessageResponse:
        concept = req.topic or req.concept or "Binary Search"
        student_id = req.user_id or req.student_id or "demo_student"
        step_idx = req.step_index if req.step_index is not None else req.current_step_index

        def fallback():
            return ChatMessageResponse(
                reply=(
                    f"Great question about {concept}! Remember that Binary Search requires the array to be sorted first. "
                    f"If the array is unsorted, we cannot know which half contains the target without checking every element."
                ),
                code=(
                    "# Binary Search Implementation in Python:\n"
                    "def binary_search(arr, target):\n"
                    "    low = 0\n"
                    "    high = len(arr) - 1\n"
                    "    while low <= high:\n"
                    "        mid = (low + high) // 2\n"
                    "        if arr[mid] == target:\n"
                    "            return mid\n"
                    "        elif arr[mid] < target:\n"
                    "            low = mid + 1\n"
                    "        else:\n"
                    "            high = mid - 1\n"
                    "    return -1\n"
                ),
                agent_thoughts="Explaining sorting precondition for binary search and providing implementation.",
                suggested_board_commands=[
                    TextCommand(
                        id="chat_note",
                        content="Key Rule: Binary Search requires sorted input!",
                        x=60,
                        y=380,
                        size=16,
                        color="#b91c1c"
                    )
                ],
                trace=AgentTrace(
                    source="fallback_canned",
                    provider="internal",
                    model="canned_socratic",
                    latency_ms=0,
                    detected_misconception="precondition_unclear",
                    strategy_chosen="socratic_explanation",
                    mastery_before=0.50,
                    mastery_after=0.55,
                    provider_used="internal"
                )
            )

        try:
            mastery_profile = learner_client.get_mastery(student_id)
            c_tag = concept.lower().replace(" ", "_")
            current_m = mastery_profile.concept_scores.get(c_tag, 0.5)
        except Exception:
            current_m = 0.5

        history_context = ""
        if req.history:
            history_context = "\nRecent Conversation History:\n" + "\n".join(
                [f"- {turn.get('role', 'user')}: {turn.get('content', '')}" for turn in req.history[-4:]]
            )

        prompt = (
            f"You are an expert AI virtual tutor teaching an interactive computer science lesson on '{concept}'.\n"
            f"Current Lesson Step Index: {step_idx}\n"
            f"Student Mastery Score: {current_m}\n"
            f"{history_context}\n"
            f"Student Message: '{req.message}'\n\n"
            f"Provide an insightful, helpful, conversational response adhering strictly to the ChatMessageResponse schema:\n"
            f"- reply: clear, pedagogically grounded response tailored to the student's mastery level\n"
            f"- code: IF the student asks how to write or implement code (e.g. 'How to write binary search in python'), "
            f"provide a clean, runnable Python code block here. Otherwise null.\n"
            f"- suggested_board_commands: optional list of whiteboard commands (text, box, arrow, equation, mermaid) to illustrate the point visually\n"
            f"- agent_thoughts: your concise internal reasoning (visible in the UI thoughts banner)"
        )

        router.reload_keys()
        # The user requested to strictly use the Groq API key for the Chat with Teacher feature
        only_prov = "groq" if router.groq_key else None

        res = router.generate_structured_sync(
            prompt=prompt,
            response_model=ChatMessageResponse,
            mock_fallback_factory=fallback,
            only_provider=only_prov
        )
        if res.trace is None:
            res.trace = AgentTrace(
                source="mock",
                provider="mock",
                model="canned",
                latency_ms=0,
                detected_misconception=None,
                strategy_chosen="conversational_guidance",
                mastery_before=current_m,
                mastery_after=current_m,
                provider_used="mock"
            )
        else:
            if res.trace.mastery_before is None:
                res.trace.mastery_before = current_m
            if res.trace.mastery_after is None:
                res.trace.mastery_after = current_m
        return res

    async def handle_chat(self, req: ChatMessageRequest) -> ChatMessageResponse:
        return self.handle_chat_sync(req)



teacher_agent = TeacherAgent()
