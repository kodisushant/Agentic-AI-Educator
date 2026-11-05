import json
import logging
import os
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

from backend.agent.schemas import (
    AttemptRecordRequest,
    AttemptRecordResponse,
    MasteryResponse,
    WeakConceptsResponse,
    WeakConceptItem,
    RecommendResponse,
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuizQuestionItem,
    FlashcardsGenerateRequest,
    FlashcardsGenerateResponse,
    FlashcardItem,
    QuizSubmitRequest,
    QuizSubmitResponse,
    QuestionResultFeedback,
)

logger = logging.getLogger("thin_client")


def _safe_import_learner():
    """Safely import Person 4's learner service without crashing if broken."""
    try:
        from backend.learner.service import learner_service
        try:
            from backend.learner.seed import seed_demo_data
            conn = learner_service._get_conn()
            cur = conn.execute("SELECT COUNT(*) FROM attempts WHERE user_id = 'demo_student'")
            if cur.fetchone()[0] == 0:
                seed_demo_data(conn)
        except Exception as seed_err:
            logger.debug(f"Learner DB auto-seed skipped: {seed_err}")
        logger.info("Learner service loaded successfully: in_process mode active")
        return learner_service, None
    except Exception as e:
        logger.warning(f"Failed to import learner service in-process ({e}). Falling back to HTTP/Mock.")
        return None, str(e)


def _safe_import_assess():
    """Safely import Person 3's assessment service without crashing if broken."""
    try:
        from backend.assess.service import assess_service
        logger.info("Assess service loaded successfully: in_process mode active")
        return assess_service, None
    except Exception as e:
        logger.warning(f"Failed to import assess service in-process ({e}). Falling back to HTTP/Mock.")
        return None, str(e)


learner_service, _learner_import_error = _safe_import_learner()
assess_service = None
_assess_import_error = None

# In-memory mock storage for demo / standalone operation
MOCK_MASTERY_DB: Dict[str, Dict[str, float]] = {
    "demo_student": {
        "binary_search_intuition": 0.90,
        "binary_search_bounds_update": 0.45,
        "binary_search_complexity": 0.80,
    }
}
MOCK_ATTEMPTS: List[Dict[str, Any]] = []


def _post_json(url: str, payload: Dict[str, Any], timeout: float = 2.0) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_json(url: str, timeout: float = 2.0) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


class LearnerClient:
    """Thin client for Person 4's Learner Model service."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.getenv("LEARNER_API_BASE_URL", "http://localhost:8000")).rstrip("/")
        self.mock_mode = os.getenv("MOCK_MODE", "true").lower() in ("true", "1", "yes")

    def has_in_process(self) -> bool:
        return learner_service is not None

    def get_mode(self) -> str:
        if learner_service is not None:
            return "in_process"
        if not self.mock_mode and self.base_url:
            return "http"
        return "mock"

    def record_attempt(self, req: AttemptRecordRequest) -> AttemptRecordResponse:
        MOCK_ATTEMPTS.append(req.model_dump())

        if not self.mock_mode:
            try:
                res = _post_json(f"{self.base_url}/learner/attempt", req.model_dump())
                return AttemptRecordResponse.model_validate(res)
            except Exception as e:
                logger.debug(f"Learner HTTP service unreachable ({e}). Trying domain service.")

        if learner_service is not None:
            try:
                return learner_service.record_attempt(req)
            except Exception as e:
                logger.warning(f"Real learner domain service failed ({e}). Falling back to mock.")

        # Mock implementation
        user_scores = MOCK_MASTERY_DB.setdefault(req.user_id, {})
        curr = user_scores.get(req.concept_tag, 0.5)
        delta = 0.15 if req.is_correct else -0.10
        new_score = round(max(0.05, min(1.0, curr + delta)), 2)
        user_scores[req.concept_tag] = new_score

        return AttemptRecordResponse(
            status="recorded",
            user_id=req.user_id,
            concept_tag=req.concept_tag,
            new_mastery_score=new_score,
            updated_at="2026-11-05T19:30:00Z"
        )

    def get_mastery(self, user_id: str) -> MasteryResponse:
        if not self.mock_mode:
            try:
                res = _get_json(f"{self.base_url}/learner/mastery/{user_id}")
                return MasteryResponse.model_validate(res)
            except Exception as e:
                logger.debug(f"Learner HTTP service unreachable ({e}). Trying domain service.")

        if learner_service is not None:
            try:
                return learner_service.get_mastery(user_id)
            except Exception as e:
                logger.warning(f"Real learner domain service failed ({e}). Falling back to mock.")

        scores = MOCK_MASTERY_DB.get(user_id, {
            "binary_search_intuition": 0.85,
            "binary_search_bounds_update": 0.50,
            "binary_search_complexity": 0.75
        })
        overall = round(sum(scores.values()) / max(1, len(scores)), 2)
        counts = {k: 2 for k in scores}
        return MasteryResponse(
            user_id=user_id,
            overall_score=overall,
            concept_scores=scores,
            attempt_counts=counts,
            last_active="2026-11-05T19:30:00Z"
        )

    def get_weak_concepts(self, user_id: str) -> WeakConceptsResponse:
        if not self.mock_mode:
            try:
                res = _get_json(f"{self.base_url}/learner/weak/{user_id}")
                return WeakConceptsResponse.model_validate(res)
            except Exception as e:
                logger.debug(f"Learner HTTP service unreachable ({e}). Trying domain service.")

        if learner_service is not None:
            try:
                return learner_service.get_weak_concepts(user_id)
            except Exception as e:
                logger.warning(f"Real learner domain service failed ({e}). Falling back to mock.")

        mastery = self.get_mastery(user_id)
        weak_items = []
        for tag, score in mastery.concept_scores.items():
            if score < 0.60:
                weak_items.append(WeakConceptItem(
                    concept_tag=tag,
                    mastery_score=score,
                    active_misconceptions=["confuses_low_with_high_shift"],
                    recommended_action="Practice interactive boundary adjustments"
                ))
        if not weak_items:
            weak_items.append(WeakConceptItem(
                concept_tag="binary_search_bounds_update",
                mastery_score=0.45,
                active_misconceptions=["confuses_low_with_high_shift"],
                recommended_action="Practice interactive boundary adjustments"
            ))
        return WeakConceptsResponse(user_id=user_id, weak_concepts=weak_items)

    def recommend_next(self, user_id: str) -> RecommendResponse:
        if not self.mock_mode:
            try:
                res = _get_json(f"{self.base_url}/learner/recommend/{user_id}")
                return RecommendResponse.model_validate(res)
            except Exception as e:
                logger.debug(f"Learner HTTP service unreachable ({e}). Trying domain service.")

        if learner_service is not None:
            try:
                return learner_service.recommend_next(user_id)
            except Exception as e:
                logger.warning(f"Real learner domain service failed ({e}). Falling back to mock.")

        weak = self.get_weak_concepts(user_id)
        target = weak.weak_concepts[0].concept_tag if weak.weak_concepts else "binary_search_bounds_update"
        return RecommendResponse(
            user_id=user_id,
            recommended_concept=target,
            reason=f"Lowest mastery score ({weak.weak_concepts[0].mastery_score if weak.weak_concepts else 0.45}) detected",
            suggested_action="quiz"
        )


class AssessClient:
    """Thin client for Person 3's Assessment service."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.getenv("ASSESS_API_BASE_URL", "http://localhost:8000")).rstrip("/")
        self.mock_mode = os.getenv("MOCK_MODE", "true").lower() in ("true", "1", "yes")

    def _resolve_service(self):
        global assess_service, _assess_import_error
        if assess_service is None and _assess_import_error is None:
            assess_service, _assess_import_error = _safe_import_assess()
        return assess_service

    def has_in_process(self) -> bool:
        return self._resolve_service() is not None

    def get_mode(self) -> str:
        if self._resolve_service() is not None:
            return "in_process"
        if not self.mock_mode and self.base_url:
            return "http"
        return "mock"

    def generate_quiz(self, req: QuizGenerateRequest) -> QuizGenerateResponse:
        if not self.mock_mode:
            try:
                res = _post_json(f"{self.base_url}/assess/quiz", req.model_dump())
                return QuizGenerateResponse.model_validate(res)
            except Exception as e:
                logger.debug(f"Assess HTTP service unreachable ({e}). Trying domain service.")

        service = self._resolve_service()
        if service is not None:
            try:
                questions = service._get_fallback_questions(req.topic, req.num_questions)
                quiz_id = f"quiz_{req.topic.lower().replace(' ', '_')}"
                service.active_quizzes[quiz_id] = {q.question_id: q for q in questions}
                return QuizGenerateResponse(
                    quiz_id=quiz_id,
                    topic=req.topic,
                    questions=questions
                )
            except Exception as e:
                logger.warning(f"Real assess domain service failed ({e}). Falling back to mock.")

        # Canned mock quiz for Binary Search
        questions = [
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
            )
        ]
        return QuizGenerateResponse(
            quiz_id="quiz_bs_101",
            topic=req.topic,
            questions=questions[:req.num_questions]
        )

    def generate_flashcards(self, req: FlashcardsGenerateRequest) -> FlashcardsGenerateResponse:
        if not self.mock_mode:
            try:
                res = _post_json(f"{self.base_url}/assess/flashcards", req.model_dump())
                return FlashcardsGenerateResponse.model_validate(res)
            except Exception as e:
                logger.debug(f"Assess HTTP service unreachable ({e}). Trying domain service.")

        service = self._resolve_service()
        if service is not None:
            try:
                cards = service._get_fallback_flashcards(req.topic, req.count)
                return FlashcardsGenerateResponse(topic=req.topic, cards=cards)
            except Exception as e:
                logger.warning(f"Real assess domain service failed ({e}). Falling back to mock.")

        cards = [
            FlashcardItem(
                card_id="fc_1",
                concept_tag="binary_search_complexity",
                front="What is the time complexity of Binary Search?",
                back="O(log n) time and O(1) auxiliary space (iterative).",
                hint="Halves search space each step."
            ),
            FlashcardItem(
                card_id="fc_2",
                concept_tag="binary_search_mid_calc",
                front="How can you calculate the midpoint to prevent integer overflow in C++/Java?",
                back="mid = low + (high - low) / 2",
                hint="Avoid adding two huge integers."
            ),
            FlashcardItem(
                card_id="fc_3",
                concept_tag="binary_search_bounds_update",
                front="When target < array[mid], what is the update?",
                back="high = mid - 1",
                hint="Search the lower half."
            ),
            FlashcardItem(
                card_id="fc_4",
                concept_tag="binary_search_termination",
                front="What is the loop termination condition for standard iterative Binary Search?",
                back="while low <= high:",
                hint="Check even when low == high."
            ),
        ]
        return FlashcardsGenerateResponse(topic=req.topic, cards=cards[:req.count])

    def submit_quiz(self, req: QuizSubmitRequest) -> QuizSubmitResponse:
        if not self.mock_mode:
            try:
                res = _post_json(f"{self.base_url}/assess/submit", req.model_dump())
                return QuizSubmitResponse.model_validate(res)
            except Exception as e:
                logger.debug(f"Assess HTTP service unreachable ({e}). Trying domain service.")

        service = self._resolve_service()
        if service is not None:
            try:
                return service.submit_quiz(req)
            except Exception as e:
                logger.warning(f"Real assess domain service failed ({e}). Falling back to mock.")

        # Evaluate against mock questions
        correct_answers = {"q_bs_1": 0, "q_bs_2": 1, "q_bs_3": 1}
        tags = {
            "q_bs_1": "binary_search_precondition",
            "q_bs_2": "binary_search_bounds_update",
            "q_bs_3": "binary_search_complexity"
        }
        feedback_list = []
        correct_count = 0

        for q_id, ans_idx in req.answers.items():
            expected = correct_answers.get(q_id, 0)
            is_corr = (ans_idx == expected)
            if is_corr:
                correct_count += 1
            feedback_list.append(QuestionResultFeedback(
                question_id=q_id,
                concept_tag=tags.get(q_id, "general"),
                is_correct=is_corr,
                selected_index=ans_idx,
                correct_index=expected,
                explanation="Correct answer verified." if is_corr else "Incorrect. Review midpoint boundary adjustment.",
                identified_misconception=None if is_corr else "confuses_boundary_adjustment"
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


learner_client = LearnerClient()
assess_client = AssessClient()
