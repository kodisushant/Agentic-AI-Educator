import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.agent.schemas import (
    AttemptRecordRequest,
    AttemptRecordResponse,
    MasteryResponse,
    WeakConceptsResponse,
    WeakConceptItem,
    RecommendResponse,
)
from backend.learner.db import get_db_connection, init_db
from backend.learner.model import (
    WEAK_MASTERY_THRESHOLD,
    calculate_decayed_score,
    generate_pedagogical_remediation,
    get_recommended_action,
    update_ewma_mastery,
)


def now_iso() -> str:
    """Return standard UTC ISO-8601 timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class LearnerService:
    """Core domain service for Student Modeling, EWMA Mastery Tracking, and Recommendations."""

    def __init__(self, connection: Optional[sqlite3.Connection] = None):
        self._conn = connection
        init_db(self._conn)

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is not None:
            return self._conn
        return get_db_connection()

    def ensure_user(self, conn: sqlite3.Connection, user_id: str, name: Optional[str] = None) -> None:
        """Ensure user record exists in database."""
        user_name = name or ("Alex Chen" if user_id == "demo_student" else user_id.replace("_", " ").title())
        ts = now_iso()
        conn.execute("""
        INSERT INTO users (id, name, email, created_at, last_active)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET last_active = excluded.last_active;
        """, (user_id, user_name, f"{user_id}@example.com", ts, ts))

    def ensure_concept(self, conn: sqlite3.Connection, concept_tag: str, topic: str = "Binary Search") -> None:
        """Ensure concept record exists in database."""
        name = concept_tag.replace("_", " ").title()
        conn.execute("""
        INSERT OR IGNORE INTO concepts (tag, name, topic, description, difficulty)
        VALUES (?, ?, ?, ?, ?);
        """, (concept_tag, name, topic, f"Core topic for {name}", "beginner"))

    def _record_single_attempt_in_tx(self, conn: sqlite3.Connection, req: AttemptRecordRequest, ts: str) -> AttemptRecordResponse:
        """Helper to record an attempt inside an active transaction."""
        self.ensure_user(conn, req.user_id)
        self.ensure_concept(conn, req.concept_tag)

        # Fetch existing mastery record
        cur = conn.execute("""
        SELECT score, attempt_count, last_attempt_at
        FROM mastery
        WHERE user_id = ? AND concept_tag = ?;
        """, (req.user_id, req.concept_tag))
        row = cur.fetchone()

        if row:
            prev_score = float(row["score"])
            attempt_count = int(row["attempt_count"]) + 1
            decayed_prev = calculate_decayed_score(prev_score, row["last_attempt_at"], ts)
        else:
            decayed_prev = 0.50  # Neutral prior for unpracticed concept
            attempt_count = 1

        # Calculate updated mastery using EWMA
        new_score = update_ewma_mastery(
            current_score=decayed_prev,
            is_correct=req.is_correct,
            time_spent_seconds=req.time_spent_seconds,
            attempt_count=attempt_count,
        )

        # Upsert into mastery table
        conn.execute("""
        INSERT INTO mastery (user_id, concept_tag, score, attempt_count, last_attempt_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, concept_tag) DO UPDATE SET
            score = excluded.score,
            attempt_count = excluded.attempt_count,
            last_attempt_at = excluded.last_attempt_at,
            updated_at = excluded.updated_at;
        """, (req.user_id, req.concept_tag, new_score, attempt_count, ts, ts))

        # Insert attempt log
        misconceptions_json = json.dumps(req.misconceptions or [])
        metadata_json = json.dumps(req.metadata or {})
        conn.execute("""
        INSERT INTO attempts (
            user_id, concept_tag, question_id, is_correct,
            time_spent_seconds, misconceptions_json, metadata_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            req.user_id,
            req.concept_tag,
            req.question_id,
            1 if req.is_correct else 0,
            req.time_spent_seconds,
            misconceptions_json,
            metadata_json,
            ts,
        ))

        # Upsert any observed misconceptions
        for misc_tag in req.misconceptions or []:
            if misc_tag and misc_tag.strip():
                conn.execute("""
                INSERT INTO misconceptions (user_id, concept_tag, misconception_tag, frequency, last_observed_at)
                VALUES (?, ?, ?, 1, ?)
                ON CONFLICT(user_id, concept_tag, misconception_tag) DO UPDATE SET
                    frequency = frequency + 1,
                    last_observed_at = excluded.last_observed_at;
                """, (req.user_id, req.concept_tag, misc_tag.strip(), ts))

        # Update user last_active
        conn.execute("UPDATE users SET last_active = ? WHERE id = ?;", (ts, req.user_id))

        return AttemptRecordResponse(
            status="recorded",
            user_id=req.user_id,
            concept_tag=req.concept_tag,
            new_mastery_score=new_score,
            updated_at=ts,
        )

    def record_attempt(self, req: AttemptRecordRequest) -> AttemptRecordResponse:
        """
        Record a student attempt on a question or exercise.
        Updates EWMA mastery with forgetting decay and persists observed misconceptions.
        """
        conn = self._get_conn()
        ts = now_iso()
        with conn:
            return self._record_single_attempt_in_tx(conn, req, ts)

    def record_attempts_batch(self, reqs: List[AttemptRecordRequest]) -> List[AttemptRecordResponse]:
        """Record multiple student attempts atomically in a single ultra-fast database transaction."""
        if not reqs:
            return []
        conn = self._get_conn()
        ts = now_iso()
        results = []
        with conn:
            for req in reqs:
                res = self._record_single_attempt_in_tx(conn, req, ts)
                results.append(res)
        return results

    def get_mastery(self, user_id: str) -> MasteryResponse:
        """Returns overall weighted mastery score and per-concept breakdown."""
        conn = self._get_conn()
        cur = conn.execute("""
        SELECT concept_tag, score, attempt_count, last_attempt_at
        FROM mastery
        WHERE user_id = ?;
        """, (user_id,))
        rows = cur.fetchall()

        if not rows:
            # Return default initial profile if no attempts yet
            return MasteryResponse(
                user_id=user_id,
                overall_score=0.50,
                concept_scores={
                    "binary_search_intuition": 0.50,
                    "binary_search_bounds_update": 0.50,
                    "binary_search_complexity": 0.50,
                },
                attempt_counts={
                    "binary_search_intuition": 0,
                    "binary_search_bounds_update": 0,
                    "binary_search_complexity": 0,
                },
                last_active=now_iso(),
            )

        scores: Dict[str, float] = {}
        counts: Dict[str, int] = {}
        latest_active = now_iso()

        for r in rows:
            tag = r["concept_tag"]
            decayed = calculate_decayed_score(float(r["score"]), r["last_attempt_at"])
            scores[tag] = round(decayed, 2)
            counts[tag] = int(r["attempt_count"])
            if r["last_attempt_at"]:
                latest_active = r["last_attempt_at"]

        overall = round(sum(scores.values()) / max(1, len(scores)), 2)

        return MasteryResponse(
            user_id=user_id,
            overall_score=overall,
            concept_scores=scores,
            attempt_counts=counts,
            last_active=latest_active,
        )

    def get_weak_concepts(
        self,
        user_id: str,
        precomputed_mastery: Optional[MasteryResponse] = None
    ) -> WeakConceptsResponse:
        """Returns concepts with mastery score < 0.60 along with active misconceptions."""
        mastery = precomputed_mastery or self.get_mastery(user_id)
        conn = self._get_conn()
        weak_list: List[WeakConceptItem] = []

        for tag, score in mastery.concept_scores.items():
            if score < WEAK_MASTERY_THRESHOLD:
                # Query active misconceptions for this concept using index
                cur = conn.execute("""
                SELECT misconception_tag, frequency
                FROM misconceptions
                WHERE user_id = ? AND concept_tag = ?
                ORDER BY frequency DESC;
                """, (user_id, tag))
                misc_rows = cur.fetchall()
                active_misconceptions = [m["misconception_tag"] for m in misc_rows]

                remediation = generate_pedagogical_remediation(tag, active_misconceptions)

                weak_list.append(WeakConceptItem(
                    concept_tag=tag,
                    mastery_score=score,
                    active_misconceptions=active_misconceptions,
                    recommended_action=remediation,
                ))

        # Sort weakest first
        weak_list.sort(key=lambda item: item.mastery_score)

        return WeakConceptsResponse(user_id=user_id, weak_concepts=weak_list)

    def recommend_next(
        self,
        user_id: str,
        precomputed_weak: Optional[WeakConceptsResponse] = None,
        precomputed_mastery: Optional[MasteryResponse] = None
    ) -> RecommendResponse:
        """Selects the highest-priority concept and optimal pedagogical action."""
        weak = precomputed_weak or self.get_weak_concepts(user_id, precomputed_mastery=precomputed_mastery)
        if weak.weak_concepts:
            target_item = weak.weak_concepts[0]
            action, rationale = get_recommended_action(target_item.mastery_score)
            return RecommendResponse(
                user_id=user_id,
                recommended_concept=target_item.concept_tag,
                reason=f"Priority practice: lowest mastery ({target_item.mastery_score:.2f}) with active misconceptions.",
                suggested_action=action,
            )

        mastery = precomputed_mastery or self.get_mastery(user_id)
        if mastery.concept_scores:
            lowest_tag = min(mastery.concept_scores, key=mastery.concept_scores.get)
            score = mastery.concept_scores[lowest_tag]
            action, rationale = get_recommended_action(score)
            return RecommendResponse(
                user_id=user_id,
                recommended_concept=lowest_tag,
                reason=f"Reinforce developing concept ({score:.2f}) for retention.",
                suggested_action=action,
            )

        return RecommendResponse(
            user_id=user_id,
            recommended_concept="binary_search_bounds_update",
            reason="Core foundational concept for Binary Search.",
            suggested_action="lesson",
        )

    def get_history(self, user_id: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Retrieve recent attempt logs for timeline visualization."""
        conn = self._get_conn()
        cur = conn.execute("""
        SELECT id, user_id, concept_tag, question_id, is_correct, time_spent_seconds,
               misconceptions_json, metadata_json, created_at
        FROM attempts
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?;
        """, (user_id, limit))
        rows = cur.fetchall()
        history = []
        for r in rows:
            history.append({
                "id": r["id"],
                "user_id": r["user_id"],
                "concept_tag": r["concept_tag"],
                "question_id": r["question_id"],
                "is_correct": bool(r["is_correct"]),
                "time_spent_seconds": float(r["time_spent_seconds"]),
                "misconceptions": json.loads(r["misconceptions_json"] or "[]"),
                "metadata": json.loads(r["metadata_json"] or "{}"),
                "created_at": r["created_at"],
            })
        return history

    def get_user_summary(self, user_id: str) -> Dict[str, Any]:
        """Aggregate summary for student profile dashboard with single-pass optimization."""
        mastery = self.get_mastery(user_id)
        weak = self.get_weak_concepts(user_id, precomputed_mastery=mastery)
        recommendation = self.recommend_next(user_id, precomputed_weak=weak, precomputed_mastery=mastery)
        history = self.get_history(user_id, limit=10)

        conn = self._get_conn()
        cur = conn.execute("SELECT name, email, created_at, last_active FROM users WHERE id = ?;", (user_id,))
        user_row = cur.fetchone()
        user_name = user_row["name"] if user_row else "Alex Chen"

        return {
            "user_id": user_id,
            "name": user_name,
            "overall_score": mastery.overall_score,
            "concept_scores": mastery.concept_scores,
            "attempt_counts": mastery.attempt_counts,
            "weak_concepts": [w.model_dump() for w in weak.weak_concepts],
            "recommendation": recommendation.model_dump(),
            "history": history,
            "total_attempts": sum(mastery.attempt_counts.values()),
        }


learner_service = LearnerService()
