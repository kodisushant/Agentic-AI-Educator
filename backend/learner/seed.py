import json
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional

from backend.learner.db import get_db_connection, init_db


def seed_demo_data(connection: Optional[sqlite3.Connection] = None) -> None:
    """Populates realistic student persona data and attempt histories."""
    conn = connection or get_db_connection()
    init_db(conn)

    now = datetime.now(timezone.utc)
    t_minus_3d = (now - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    t_minus_2d = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    t_minus_1d = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    t_minus_2h = (now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    t_minus_10m = (now - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    t_now = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        with conn:
            # 1. Seed Users
            conn.execute("""
            INSERT INTO users (id, name, email, created_at, last_active)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET last_active = excluded.last_active;
            """, ("demo_student", "Alex Chen", "alex.chen@student.edu", t_minus_3d, t_minus_10m))

            conn.execute("""
            INSERT INTO users (id, name, email, created_at, last_active)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET last_active = excluded.last_active;
            """, ("novice_learner", "Maya Patel", "maya.patel@student.edu", t_minus_1d, t_minus_1d))

            # 2. Seed Concepts
            concepts = [
                ("binary_search_intuition", "Binary Search Intuition", "Binary Search", "Core concept of dividing search space in half", "beginner"),
                ("binary_search_bounds_update", "Binary Search Bounds Update", "Binary Search", "Adjusting low and high pointers correctly based on midpoint comparison", "intermediate"),
                ("binary_search_complexity", "Time Complexity Analysis", "Binary Search", "Understanding O(log n) logarithmic reduction", "intermediate"),
                ("binary_search_edge_cases", "Edge Cases & Termination", "Binary Search", "Handling duplicate elements, missing targets, and empty arrays", "advanced"),
            ]
            for tag, name, topic, desc, diff in concepts:
                conn.execute("""
                INSERT OR REPLACE INTO concepts (tag, name, topic, description, difficulty)
                VALUES (?, ?, ?, ?, ?);
                """, (tag, name, topic, desc, diff))

            # 3. Clear and re-populate demo attempts & mastery
            conn.execute("DELETE FROM attempts WHERE user_id = 'demo_student';")
            conn.execute("DELETE FROM mastery WHERE user_id = 'demo_student';")
            conn.execute("DELETE FROM misconceptions WHERE user_id = 'demo_student';")

            attempts = [
                # Intuition attempts (3 correct)
                ("demo_student", "binary_search_intuition", "q_bs_intuition_1", 1, 8.5, "[]", "{\"context\":\"lesson_check\"}", t_minus_3d),
                ("demo_student", "binary_search_intuition", "q_bs_intuition_2", 1, 7.2, "[]", "{\"context\":\"quiz_1\"}", t_minus_2d),
                ("demo_student", "binary_search_intuition", "q_bs_intuition_3", 1, 6.0, "[]", "{\"context\":\"quiz_1\"}", t_minus_2d),

                # Bounds update attempts (1 correct, 3 wrong with misconceptions)
                ("demo_student", "binary_search_bounds_update", "q_bs_bounds_1", 0, 24.0, "[\"confuses_direction_when_target_greater\"]", "{\"context\":\"lesson_step_2\"}", t_minus_2d),
                ("demo_student", "binary_search_bounds_update", "q_bs_bounds_2", 0, 18.5, "[\"confuses_direction_when_target_greater\", \"confuses_low_with_high_shift\"]", "{\"context\":\"practice\"}", t_minus_1d),
                ("demo_student", "binary_search_bounds_update", "q_bs_bounds_3", 1, 15.0, "[]", "{\"context\":\"remediation_check\"}", t_minus_2h),
                ("demo_student", "binary_search_bounds_update", "q_bs_bounds_4", 0, 22.0, "[\"fails_to_exclude_checked_midpoint\"]", "{\"context\":\"quiz_checkpoint\"}", t_minus_10m),

                # Complexity attempts (2 correct)
                ("demo_student", "binary_search_complexity", "q_bs_complex_1", 1, 9.0, "[]", "{\"context\":\"flashcard\"}", t_minus_2d),
                ("demo_student", "binary_search_complexity", "q_bs_complex_2", 1, 11.0, "[]", "{\"context\":\"quiz_checkpoint\"}", t_minus_1d),

                # Edge cases attempts (1 correct, 1 wrong)
                ("demo_student", "binary_search_edge_cases", "q_bs_edge_1", 0, 35.0, "[\"infinite_loop_on_two_elements\"]", "{\"context\":\"live_code_exercise\"}", t_minus_1d),
                ("demo_student", "binary_search_edge_cases", "q_bs_edge_2", 1, 14.0, "[]", "{\"context\":\"practice\"}", t_minus_2h),
            ]

            for u_id, c_tag, q_id, is_corr, t_spent, misc_json, meta_json, created_at in attempts:
                conn.execute("""
                INSERT INTO attempts (user_id, concept_tag, question_id, is_correct, time_spent_seconds, misconceptions_json, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (u_id, c_tag, q_id, is_corr, t_spent, misc_json, meta_json, created_at))

            # 4. Mastery table initial values
            mastery_data = [
                ("demo_student", "binary_search_intuition", 0.90, 3, t_minus_2d, t_minus_2d),
                ("demo_student", "binary_search_bounds_update", 0.45, 4, t_minus_10m, t_minus_10m),
                ("demo_student", "binary_search_complexity", 0.80, 2, t_minus_1d, t_minus_1d),
                ("demo_student", "binary_search_edge_cases", 0.55, 2, t_minus_2h, t_minus_2h),
            ]
            for u_id, c_tag, score, count, last_at, updated_at in mastery_data:
                conn.execute("""
                INSERT INTO mastery (user_id, concept_tag, score, attempt_count, last_attempt_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """, (u_id, c_tag, score, count, last_at, updated_at))

            # 5. Misconceptions table values
            misconceptions_data = [
                ("demo_student", "binary_search_bounds_update", "confuses_direction_when_target_greater", 2, t_minus_1d),
                ("demo_student", "binary_search_bounds_update", "confuses_low_with_high_shift", 1, t_minus_1d),
                ("demo_student", "binary_search_bounds_update", "fails_to_exclude_checked_midpoint", 1, t_minus_10m),
                ("demo_student", "binary_search_edge_cases", "infinite_loop_on_two_elements", 1, t_minus_1d),
            ]
            for u_id, c_tag, m_tag, freq, last_obs in misconceptions_data:
                conn.execute("""
                INSERT INTO misconceptions (user_id, concept_tag, misconception_tag, frequency, last_observed_at)
                VALUES (?, ?, ?, ?, ?);
                """, (u_id, c_tag, m_tag, freq, last_obs))

    finally:
        if connection is None:
            conn.close()


if __name__ == "__main__":
    seed_demo_data()
    print("✓ Successfully initialized and seeded SQLite Learner DB.")
