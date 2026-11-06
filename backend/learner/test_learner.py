import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.agent.schemas import (
    AttemptRecordRequest,
    AttemptRecordResponse,
    MasteryResponse,
    WeakConceptsResponse,
    RecommendResponse,
)
from backend.learner.db import init_db
from backend.learner.model import (
    calculate_decayed_score,
    get_recommended_action,
    update_ewma_mastery,
)
from backend.learner.seed import seed_demo_data
from backend.learner.service import LearnerService


class TestLearnerModel(unittest.TestCase):
    def setUp(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
            self.temp_db_path = tf.name
        self.conn = sqlite3.connect(self.temp_db_path)
        self.conn.row_factory = sqlite3.Row
        init_db(self.conn)
        seed_demo_data(self.conn)
        self.service = LearnerService(connection=self.conn)

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except Exception:
                pass

    def test_ewma_calculation_and_decay(self):
        initial_score = 0.50
        correct_score = update_ewma_mastery(initial_score, is_correct=True, time_spent_seconds=12.0)
        self.assertGreater(correct_score, initial_score)

        wrong_score = update_ewma_mastery(correct_score, is_correct=False, time_spent_seconds=20.0)
        self.assertLess(wrong_score, correct_score)

        decayed = calculate_decayed_score(0.90, "2026-11-01T00:00:00Z", "2026-11-05T00:00:00Z")
        self.assertLess(decayed, 0.90)

    def test_get_mastery(self):
        mastery = self.service.get_mastery("demo_student")
        self.assertIsInstance(mastery, MasteryResponse)
        self.assertIn("binary_search_bounds_update", mastery.concept_scores)
        self.assertLessEqual(mastery.concept_scores["binary_search_bounds_update"], 0.55)
        self.assertGreaterEqual(mastery.concept_scores["binary_search_intuition"], 0.80)

    def test_get_weak_concepts(self):
        weak = self.service.get_weak_concepts("demo_student")
        self.assertIsInstance(weak, WeakConceptsResponse)
        self.assertGreaterEqual(len(weak.weak_concepts), 1)
        weak_tags = [w.concept_tag for w in weak.weak_concepts]
        self.assertIn("binary_search_bounds_update", weak_tags)

    def test_recommend_next(self):
        rec = self.service.recommend_next("demo_student")
        self.assertIsInstance(rec, RecommendResponse)
        self.assertEqual(rec.recommended_concept, "binary_search_bounds_update")
        self.assertIn(rec.suggested_action, ["lesson", "quiz"])

    def test_record_attempt_and_history(self):
        new_attempt = AttemptRecordRequest(
            user_id="demo_student",
            concept_tag="binary_search_bounds_update",
            is_correct=True,
            time_spent_seconds=10.0,
            question_id="remediation_test_1",
            misconceptions=[]
        )
        res = self.service.record_attempt(new_attempt)
        self.assertIsInstance(res, AttemptRecordResponse)

        history = self.service.get_history("demo_student", limit=5)
        self.assertGreaterEqual(len(history), 1)
        self.assertEqual(history[0]["question_id"], "remediation_test_1")
        self.assertTrue(history[0]["is_correct"])

    def test_record_attempts_batch_atomic(self):
        batch = [
            AttemptRecordRequest(user_id="demo_student", concept_tag="binary_search_bounds_update", is_correct=True, time_spent_seconds=8.0, question_id="batch_1"),
            AttemptRecordRequest(user_id="demo_student", concept_tag="binary_search_complexity", is_correct=True, time_spent_seconds=5.0, question_id="batch_2"),
        ]
        results = self.service.record_attempts_batch(batch)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].status, "recorded")
        self.assertEqual(results[1].status, "recorded")

    def test_get_user_summary_fast(self):
        summary = self.service.get_user_summary("demo_student")
        self.assertEqual(summary["user_id"], "demo_student")
        self.assertIn("overall_score", summary)
        self.assertIn("concept_scores", summary)
        self.assertIn("weak_concepts", summary)
        self.assertIn("recommendation", summary)
        self.assertIn("history", summary)


if __name__ == "__main__":
    unittest.main()
