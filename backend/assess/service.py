import logging
import uuid
from typing import Dict, List, Optional
from datetime import datetime, timezone

from backend.agent.schemas import (
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuizQuestionItem,
    FlashcardsGenerateRequest,
    FlashcardsGenerateResponse,
    FlashcardItem,
    QuizSubmitRequest,
    QuizSubmitResponse,
    QuestionResultFeedback,
    AttemptRecordRequest,
)
from backend.agent.llm_router import router
from backend.agent.client import learner_client

logger = logging.getLogger("assess_service")


# Canned topic question bank for fallback / mock mode / resilience
TOPIC_QUESTION_BANK: Dict[str, List[QuizQuestionItem]] = {
    "binary search": [
        QuizQuestionItem(
            question_id="q_bs_1",
            concept_tag="binary_search_precondition",
            question="What is the mandatory prerequisite before applying Binary Search on a collection?",
            options=[
                "The elements must be sorted",
                "The elements must all be unique",
                "The list length must be a power of two",
                "The array must fit in cache"
            ],
            correct_index=0,
            explanation="Binary search relies on order to discard halves. Without sorting, half-elimination is invalid."
        ),
        QuizQuestionItem(
            question_id="q_bs_2",
            concept_tag="binary_search_bounds_update",
            question="If array[mid] < target in a standard ascending search, how are pointers updated?",
            options=[
                "high = mid - 1",
                "low = mid + 1",
                "low = mid",
                "high = mid"
            ],
            correct_index=1,
            explanation="Since the target is strictly larger than array[mid], we eliminate the left half up to mid."
        ),
        QuizQuestionItem(
            question_id="q_bs_3",
            concept_tag="binary_search_complexity",
            question="What is the worst-case time complexity of Binary Search on an array of size n?",
            options=[
                "O(1)",
                "O(log n)",
                "O(n)",
                "O(n log n)"
            ],
            correct_index=1,
            explanation="At each comparison the problem size halves: n -> n/2 -> n/4 -> ... -> 1, taking log2(n) steps."
        ),
        QuizQuestionItem(
            question_id="q_bs_4",
            concept_tag="binary_search_termination",
            question="What is the correct loop condition for standard iterative Binary Search?",
            options=[
                "while low < high",
                "while low <= high",
                "while low != high",
                "while mid >= 0"
            ],
            correct_index=1,
            explanation="`low <= high` ensures the 1-element case (where low == high) is inspected."
        ),
        QuizQuestionItem(
            question_id="q_bs_5",
            concept_tag="binary_search_mid_calc",
            question="How can you calculate midpoint to prevent integer overflow in fixed-width languages?",
            options=[
                "mid = (low + high) // 2",
                "mid = low + (high - low) // 2",
                "mid = high - (low // 2)",
                "mid = low * 2 + high"
            ],
            correct_index=1,
            explanation="`low + (high - low) // 2` computes the exact same value without risking low + high exceeding integer bounds."
        )
    ],
    "recursion": [
        QuizQuestionItem(
            question_id="q_rec_1",
            concept_tag="recursion_base_case",
            question="What happens if a recursive function does not define or reach a valid base case?",
            options=[
                "The function returns None",
                "A RecursionError / stack overflow occurs",
                "The loop converts to an iterative loop",
                "Python optimizes it with tail-call elimination"
            ],
            correct_index=1,
            explanation="Without a base case, calls pile onto the execution call stack until the maximum stack depth is exceeded."
        ),
        QuizQuestionItem(
            question_id="q_rec_2",
            concept_tag="recursion_call_stack",
            question="In which order do suspended stack frames resolve in a recursive process?",
            options=[
                "First-In, First-Out (FIFO)",
                "Last-In, First-Out (LIFO)",
                "Random order",
                "Simultaneously via multithreading"
            ],
            correct_index=1,
            explanation="The call stack is a LIFO structure: the deepest child call resolves before its caller can continue."
        )
    ]
}

TOPIC_FLASHCARD_BANK: Dict[str, List[FlashcardItem]] = {
    "binary search": [
        FlashcardItem(
            card_id="fc_bs_1",
            concept_tag="binary_search_complexity",
            front="What is the time complexity of Binary Search?",
            back="O(log n) worst/average case, O(1) best case. Auxiliary space is O(1) for iterative.",
            hint="The search space cuts in half every iteration."
        ),
        FlashcardItem(
            card_id="fc_bs_2",
            concept_tag="binary_search_bounds_update",
            front="When target < array[mid], which pointer moves and how?",
            back="high = mid - 1",
            hint="Target must be strictly in the lower subarray."
        ),
        FlashcardItem(
            card_id="fc_bs_3",
            concept_tag="binary_search_precondition",
            front="What requirement must be satisfied before Binary Search can be applied?",
            back="The collection must be sorted in monotonic order (or have a monotonic predicate).",
            hint="Order is required to discard half the elements safely."
        ),
        FlashcardItem(
            card_id="fc_bs_4",
            concept_tag="binary_search_mid_calc",
            front="How do you compute mid without integer overflow?",
            back="mid = low + (high - low) // 2",
            hint="Avoid low + high directly."
        ),
        FlashcardItem(
            card_id="fc_bs_5",
            concept_tag="binary_search_termination",
            front="Why is `while low <= high:` used instead of `while low < high:`?",
            back="To check the final remaining element when low and high point to the same index.",
            hint="Single element range."
        )
    ],
    "recursion": [
        FlashcardItem(
            card_id="fc_rec_1",
            concept_tag="recursion_base_case",
            front="What is a recursive base case?",
            back="The non-recursive condition that terminates the chain of recursive calls.",
            hint="Prevents infinite loop."
        ),
        FlashcardItem(
            card_id="fc_rec_2",
            concept_tag="recursion_call_stack",
            front="What data structure manages active function invocations during recursion?",
            back="The execution Call Stack (operating on LIFO order).",
            hint="Piles frames."
        )
    ]
}


class AssessmentService:
    """
    Assessment Service for Person 3.
    Generates schema-validated quizzes & flashcards, evaluates student responses,
    and publishes attempt records to Person 4's Learner Model.
    """

    def __init__(self):
        # In-memory storage for active quizzes for validation
        self.active_quizzes: Dict[str, Dict[str, QuizQuestionItem]] = {}

    def _get_fallback_questions(self, topic: str, count: int) -> List[QuizQuestionItem]:
        normalized = topic.strip().lower()
        questions = TOPIC_QUESTION_BANK.get(normalized)
        if not questions:
            for key, bank in TOPIC_QUESTION_BANK.items():
                if key in normalized or normalized in key:
                    questions = bank
                    break
        if not questions:
            questions = TOPIC_QUESTION_BANK["binary search"]

        # Ensure unique IDs for this instance
        res = []
        for i, q in enumerate(questions[:count]):
            res.append(QuizQuestionItem(
                question_id=f"q_{i+1}_{uuid.uuid4().hex[:6]}",
                concept_tag=q.concept_tag,
                question=q.question,
                options=q.options,
                correct_index=q.correct_index,
                explanation=q.explanation
            ))
        return res

    def _get_fallback_flashcards(self, topic: str, count: int) -> List[FlashcardItem]:
        normalized = topic.strip().lower()
        cards = TOPIC_FLASHCARD_BANK.get(normalized)
        if not cards:
            for key, bank in TOPIC_FLASHCARD_BANK.items():
                if key in normalized or normalized in key:
                    cards = bank
                    break
        if not cards:
            cards = TOPIC_FLASHCARD_BANK["binary search"]

        res = []
        for i, c in enumerate(cards[:count]):
            res.append(FlashcardItem(
                card_id=f"fc_{i+1}_{uuid.uuid4().hex[:6]}",
                concept_tag=c.concept_tag,
                front=c.front,
                back=c.back,
                hint=c.hint
            ))
        return res

    async def generate_quiz(self, req: QuizGenerateRequest) -> QuizGenerateResponse:
        """
        Generate an MCQ quiz targeted to topic and weak concepts.
        Uses LLM via llm_router when configured, validated against QuizGenerateResponse.
        Falls back reliably to curated bank on timeout, rate limits, or mock mode.
        """
        quiz_id = f"quiz_{uuid.uuid4().hex[:8]}"

        # Attempt LLM generation if router has live keys and not in mock mode
        if not router.mock_mode and (router.gemini_key or router.groq_key or router.cerebras_key or router.openrouter_key):
            weak_context = ", ".join(req.weak_concepts) if req.weak_concepts else "general fundamentals"
            prompt = (
                f"You are an expert interactive CS instructor. Create a multiple choice quiz on '{req.topic}'.\n"
                f"Target these student weak concepts: {weak_context}.\n"
                f"Generate exactly {req.num_questions} multiple choice questions.\n"
                f"For each question, provide:\n"
                f"- question_id: unique string\n"
                f"- concept_tag: snake_case identifier\n"
                f"- question: clear, precise question\n"
                f"- options: list of exactly 4 strings\n"
                f"- correct_index: integer 0 to 3\n"
                f"- explanation: pedagogical explanation of why the correct option is right"
            )
            try:
                llm_res = await router.generate_structured(
                    prompt=prompt,
                    response_model=QuizGenerateResponse,
                    temperature=0.3
                )
                if llm_res and llm_res.questions:
                    llm_res.quiz_id = quiz_id
                    llm_res.topic = req.topic
                    llm_res.questions = llm_res.questions[:req.num_questions]
                    # Cache in active quizzes for submit verification
                    self.active_quizzes[quiz_id] = {q.question_id: q for q in llm_res.questions}
                    return llm_res
            except Exception as e:
                logger.warning(f"LLM quiz generation failed ({e}). Falling back to question bank.")

        # Reliable fallback
        questions = self._get_fallback_questions(req.topic, req.num_questions)
        self.active_quizzes[quiz_id] = {q.question_id: q for q in questions}

        return QuizGenerateResponse(
            quiz_id=quiz_id,
            topic=req.topic,
            questions=questions
        )

    async def generate_flashcards(self, req: FlashcardsGenerateRequest) -> FlashcardsGenerateResponse:
        """
        Generate spaced-repetition flashcard prompt/answer pairs.
        Uses LLM router when configured, with schema validation and fallback.
        """
        if not router.mock_mode and (router.gemini_key or router.groq_key or router.cerebras_key or router.openrouter_key):
            weak_context = ", ".join(req.weak_concepts) if req.weak_concepts else "fundamentals"
            prompt = (
                f"Generate {req.count} spaced-repetition flashcards for students learning '{req.topic}'.\n"
                f"Emphasize weak areas: {weak_context}.\n"
                f"Each card must contain card_id, concept_tag (snake_case), front (concise question/prompt), "
                f"back (clear explanation/answer), and optional hint."
            )
            try:
                llm_res = await router.generate_structured(
                    prompt=prompt,
                    response_model=FlashcardsGenerateResponse,
                    temperature=0.3
                )
                if llm_res and llm_res.cards:
                    llm_res.topic = req.topic
                    llm_res.cards = llm_res.cards[:req.count]
                    return llm_res
            except Exception as e:
                logger.warning(f"LLM flashcards generation failed ({e}). Falling back to flashcard bank.")

        cards = self._get_fallback_flashcards(req.topic, req.count)
        return FlashcardsGenerateResponse(
            topic=req.topic,
            cards=cards
        )

    def submit_quiz(self, req: QuizSubmitRequest) -> QuizSubmitResponse:
        """
        Evaluate student quiz answers, generate feedback, and post attempts
        to Person 4's Learner Model via learner_client.record_attempt.
        """
        questions_map = self.active_quizzes.get(req.quiz_id, {})
        feedback_list: List[QuestionResultFeedback] = []
        correct_count = 0

        # If quiz_id not cached in memory, synthesize question lookups from fallback bank
        if not questions_map:
            fallback_qs = self._get_fallback_questions("Binary Search", len(req.answers) or 3)
            # Match by question_id or fallback positionally
            for idx, (qid, ans) in enumerate(req.answers.items()):
                matched = fallback_qs[idx % len(fallback_qs)]
                questions_map[qid] = QuizQuestionItem(
                    question_id=qid,
                    concept_tag=matched.concept_tag,
                    question=matched.question,
                    options=matched.options,
                    correct_index=matched.correct_index,
                    explanation=matched.explanation
                )

        now_str = datetime.now(timezone.utc).isoformat()

        for q_id, selected_idx in req.answers.items():
            q_item = questions_map.get(q_id)
            if not q_item:
                is_correct = False
                correct_idx = 0
                concept_tag = "general_practice"
                explanation = "Question evaluation completed."
                misconception = "unrecognized_question_attempt"
            else:
                correct_idx = q_item.correct_index
                is_correct = (selected_idx == correct_idx)
                concept_tag = q_item.concept_tag
                explanation = q_item.explanation
                misconception = None if is_correct else f"misunderstands_{concept_tag}"

            if is_correct:
                correct_count += 1

            # Submit attempt to Person 4's Learner API contract
            try:
                attempt_req = AttemptRecordRequest(
                    user_id=req.user_id,
                    concept_tag=concept_tag,
                    is_correct=is_correct,
                    selected_answer=str(selected_idx),
                    time_taken_seconds=10.0,
                    misconception_tag=misconception
                )
                learner_client.record_attempt(attempt_req)
            except Exception as e:
                logger.error(f"Failed to record student attempt to learner service: {e}")

            feedback_list.append(QuestionResultFeedback(
                question_id=q_id,
                concept_tag=concept_tag,
                is_correct=is_correct,
                selected_index=selected_idx,
                correct_index=correct_idx,
                explanation=explanation,
                identified_misconception=misconception
            ))

        total = max(1, len(req.answers))
        score = round(correct_count / total, 2)

        return QuizSubmitResponse(
            quiz_id=req.quiz_id,
            user_id=req.user_id,
            score=score,
            total_questions=total,
            correct_count=correct_count,
            feedback=feedback_list
        )


assess_service = AssessmentService()

