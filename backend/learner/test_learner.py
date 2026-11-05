import os
import sqlite3
import tempfile
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


def run_learner_tests():
    print("=== Running Learner Model Unit Tests ===")

    # 1. Test EWMA calculation and Decay
    initial_score = 0.50
    # Correct answer should raise score
    correct_score = update_ewma_mastery(initial_score, is_correct=True, time_spent_seconds=12.0)
    assert correct_score > initial_score, f"Expected score to increase, got {correct_score}"
    print(f"✓ EWMA score on correct answer: {initial_score} -> {correct_score}")

    # Incorrect answer should lower score
    wrong_score = update_ewma_mastery(correct_score, is_correct=False, time_spent_seconds=20.0)
    assert wrong_score < correct_score, f"Expected score to decrease, got {wrong_score}"
    print(f"✓ EWMA score on incorrect answer: {correct_score} -> {wrong_score}")

    # Decay check
    decayed = calculate_decayed_score(0.90, "2026-11-01T00:00:00Z", "2026-11-05T00:00:00Z")
    assert decayed < 0.90, f"Expected decay over 4 days, got {decayed}"
    print(f"✓ Ebbinghaus temporal forgetting decay: 0.90 -> {decayed}")

    # 2. Test in an isolated temporary SQLite database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        temp_db_path = tf.name

    try:
        conn = sqlite3.connect(temp_db_path)
        conn.row_factory = sqlite3.Row
        init_db(conn)
        seed_demo_data(conn)
        print("✓ SQLite temporary schema initialized and seeded")

        service = LearnerService(connection=conn)

        # 3. Test get_mastery
        mastery = service.get_mastery("demo_student")
        assert isinstance(mastery, MasteryResponse)
        assert "binary_search_bounds_update" in mastery.concept_scores
        assert mastery.concept_scores["binary_search_bounds_update"] <= 0.55
        assert mastery.concept_scores["binary_search_intuition"] >= 0.80
        print(f"✓ Mastery scores verified: overall={mastery.overall_score}, scores={mastery.concept_scores}")

        # 4. Test get_weak_concepts
        weak = service.get_weak_concepts("demo_student")
        assert isinstance(weak, WeakConceptsResponse)
        assert len(weak.weak_concepts) >= 1
        weak_tags = [w.concept_tag for w in weak.weak_concepts]
        assert "binary_search_bounds_update" in weak_tags
        bounds_item = next(w for w in weak.weak_concepts if w.concept_tag == "binary_search_bounds_update")
        assert "confuses_direction_when_target_greater" in bounds_item.active_misconceptions
        print(f"✓ Weak concepts diagnosed: {weak_tags}")
        print(f"✓ Misconceptions linked: {bounds_item.active_misconceptions}")
        print(f"✓ Pedagogical recommendation: {bounds_item.recommended_action}")

        # 5. Test recommend_next
        rec = service.recommend_next("demo_student")
        assert isinstance(rec, RecommendResponse)
        assert rec.recommended_concept == "binary_search_bounds_update"
        assert rec.suggested_action in ["lesson", "quiz"]
        print(f"✓ Next recommendation verified: {rec.recommended_concept} ({rec.suggested_action}) - {rec.reason}")

        # 6. Test recording new attempt
        new_attempt = AttemptRecordRequest(
            user_id="demo_student",
            concept_tag="binary_search_bounds_update",
            is_correct=True,
            time_spent_seconds=10.0,
            question_id="remediation_test_1",
            misconceptions=[]
        )
        res = service.record_attempt(new_attempt)
        assert isinstance(res, AttemptRecordResponse)
        assert res.new_mastery_score > bounds_item.mastery_score
        print(f"✓ New successful attempt recorded: mastery improved to {res.new_mastery_score}")

        # Verify history log
        history = service.get_history("demo_student", limit=5)
        assert len(history) >= 1
        assert history[0]["question_id"] == "remediation_test_1"
        assert history[0]["is_correct"] is True
        print(f"✓ Attempt history logging verified: {len(history)} entries retrieved")

        conn.close()
    finally:
        if os.path.exists(temp_db_path):
            try:
                os.remove(temp_db_path)
            except Exception:
                pass

    print("\n✓ ALL LEARNER MODEL TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_learner_tests()
