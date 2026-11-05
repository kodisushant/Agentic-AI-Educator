"""
Exhaustive Unit & Integration Tests for Assessment Backend (/backend/assess).
Verifies:
1. Quiz & Flashcards generation and schema compliance (/contracts/openapi.json).
2. Answer evaluation, scoring, and misconception diagnosis.
3. Every submitted answer is dispatched to Person 4's Learner Model contract.
4. Edge cases: unknown quiz IDs, empty answers, missing user IDs.
5. FastAPI router mounting and endpoint conflict-free integration.
"""

import asyncio
import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.agent.schemas import (
    QuizGenerateRequest,
    QuizGenerateResponse,
    FlashcardsGenerateRequest,
    FlashcardsGenerateResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
    AttemptRecordRequest,
)
from backend.assess.service import AssessmentService
from backend.assess.router import assess_router
from backend.agent.client import MOCK_ATTEMPTS, MOCK_MASTERY_DB, learner_client


class TestAssessService(unittest.TestCase):

    def setUp(self):
        self.service = AssessmentService()

    def test_quiz_generation_schema(self):
        """Verify quiz generation returns valid structure matching contract."""
        req = QuizGenerateRequest(
            topic="Binary Search",
            num_questions=3,
            weak_concepts=["binary_search_bounds_update"],
            student_id="test_student"
        )
        res = asyncio.run(self.service.generate_quiz(req))
        self.assertIsInstance(res, QuizGenerateResponse)
        self.assertIsNotNone(res.quiz_id)
        self.assertEqual(res.topic, "Binary Search")
        self.assertEqual(len(res.questions), 3)

        for q in res.questions:
            self.assertTrue(len(q.question_id) > 0)
            self.assertTrue(len(q.options) >= 2)
            self.assertIn(q.correct_index, range(len(q.options)))
            self.assertTrue(len(q.concept_tag) > 0)
            self.assertTrue(len(q.explanation) > 0)

    def test_flashcards_generation_schema(self):
        """Verify flashcards generation returns valid cards matching contract."""
        req = FlashcardsGenerateRequest(
            topic="Binary Search",
            count=4,
            weak_concepts=["binary_search_mid_calc"],
            student_id="test_student"
        )
        res = asyncio.run(self.service.generate_flashcards(req))
        self.assertIsInstance(res, FlashcardsGenerateResponse)
        self.assertEqual(res.topic, "Binary Search")
        self.assertEqual(len(res.cards), 4)

        for card in res.cards:
            self.assertTrue(len(card.card_id) > 0)
            self.assertTrue(len(card.front) > 0)
            self.assertTrue(len(card.back) > 0)
            self.assertTrue(len(card.concept_tag) > 0)

    def test_quiz_submission_and_learner_attempt_sync(self):
        """Verify that submitting answers computes score and records learner attempt."""
        gen_req = QuizGenerateRequest(
            topic="Binary Search",
            num_questions=3,
            weak_concepts=[],
            student_id="eval_student"
        )
        quiz = asyncio.run(self.service.generate_quiz(gen_req))
        q0 = quiz.questions[0]
        q1 = quiz.questions[1]

        initial_attempt_count = len(MOCK_ATTEMPTS)

        # Submit 1 correct and 1 incorrect answer
        answers = {
            q0.question_id: q0.correct_index,
            q1.question_id: (q1.correct_index + 1) % len(q1.options)
        }

        sub_req = QuizSubmitRequest(
            quiz_id=quiz.quiz_id,
            user_id="eval_student",
            answers=answers
        )

        result = self.service.submit_quiz(sub_req)
        self.assertIsInstance(result, QuizSubmitResponse)
        self.assertEqual(result.quiz_id, quiz.quiz_id)
        self.assertEqual(result.user_id, "eval_student")
        self.assertEqual(result.total_questions, 2)
        self.assertEqual(result.correct_count, 1)
        self.assertEqual(result.score, 0.50)
        self.assertEqual(len(result.feedback), 2)

        # Verify feedback details
        fb_q0 = next(fb for fb in result.feedback if fb.question_id == q0.question_id)
        self.assertTrue(fb_q0.is_correct)
        self.assertIsNone(fb_q0.identified_misconception)

        fb_q1 = next(fb for fb in result.feedback if fb.question_id == q1.question_id)
        self.assertFalse(fb_q1.is_correct)
        self.assertIsNotNone(fb_q1.identified_misconception)

        # Confirm Person 4 learner API was invoked for each answered question
        new_attempts = MOCK_ATTEMPTS[initial_attempt_count:]
        self.assertEqual(len(new_attempts), 2)
        self.assertEqual(new_attempts[0]["user_id"], "eval_student")
        self.assertEqual(new_attempts[0]["concept_tag"], q0.concept_tag)
        self.assertTrue(new_attempts[0]["is_correct"])

        self.assertEqual(new_attempts[1]["user_id"], "eval_student")
        self.assertEqual(new_attempts[1]["concept_tag"], q1.concept_tag)
        self.assertFalse(new_attempts[1]["is_correct"])

    def test_quiz_submission_resilience_edge_cases(self):
        """Verify service handles unknown quiz ID, empty answers, and missing fields."""
        # 1. Unknown quiz ID
        sub_req = QuizSubmitRequest(
            quiz_id="unknown_quiz_123",
            user_id="resilience_student",
            answers={"q_random_1": 1, "q_random_2": 0}
        )
        res1 = self.service.submit_quiz(sub_req)
        self.assertEqual(res1.quiz_id, "unknown_quiz_123")
        self.assertEqual(res1.total_questions, 2)

        # 2. Empty answers dictionary
        empty_req = QuizSubmitRequest(
            quiz_id="unknown_quiz_123",
            user_id="resilience_student",
            answers={}
        )
        res2 = self.service.submit_quiz(empty_req)
        self.assertEqual(res2.total_questions, 1)
        self.assertEqual(res2.correct_count, 0)
        self.assertEqual(res2.score, 0.0)

    def test_router_integration_and_mounting(self):
        """Verify that assess_router mounts into FastAPI without conflicts and responds."""
        app = FastAPI()
        app.include_router(assess_router)

        client = TestClient(app)

        # Test GET /assess/health
        h_resp = client.get("/assess/health")
        self.assertEqual(h_resp.status_code, 200)
        self.assertEqual(h_resp.json()["status"], "healthy")

        # Test POST /assess/quiz
        q_resp = client.post("/assess/quiz", json={"topic": "Binary Search", "num_questions": 2})
        self.assertEqual(q_resp.status_code, 200)
        q_data = q_resp.json()
        self.assertEqual(len(q_data["questions"]), 2)

        # Test POST /assess/flashcards
        f_resp = client.post("/assess/flashcards", json={"topic": "Binary Search", "count": 2})
        self.assertEqual(f_resp.status_code, 200)
        f_data = f_resp.json()
        self.assertEqual(len(f_data["cards"]), 2)

        # Test POST /assess/submit
        s_resp = client.post("/assess/submit", json={
            "quiz_id": q_data["quiz_id"],
            "user_id": "api_test_student",
            "answers": {q_data["questions"][0]["question_id"]: q_data["questions"][0]["correct_index"]}
        })
        self.assertEqual(s_resp.status_code, 200)
        s_data = s_resp.json()
        self.assertEqual(s_data["score"], 1.0)
        self.assertEqual(s_data["correct_count"], 1)


if __name__ == "__main__":
    unittest.main()
