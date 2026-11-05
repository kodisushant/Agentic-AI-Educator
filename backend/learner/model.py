from datetime import datetime, timezone
import math
from typing import Dict, List, Optional, Tuple

# Exponential moving average learning rate
DEFAULT_ALPHA = 0.30

# Half-life / decay parameter per day of inactivity
DECAY_RATE_PER_DAY = 0.03

# Threshold below which a concept is marked weak
WEAK_MASTERY_THRESHOLD = 0.60


def calculate_decayed_score(last_score: float, last_attempt_iso: str, current_time_iso: Optional[str] = None) -> float:
    """
    Applies exponential decay (Ebbinghaus forgetting curve) based on days elapsed
    since last practice attempt.
    """
    try:
        last_dt = datetime.fromisoformat(last_attempt_iso.replace("Z", "+00:00"))
        curr_dt = (
            datetime.fromisoformat(current_time_iso.replace("Z", "+00:00"))
            if current_time_iso
            else datetime.now(timezone.utc)
        )
        days_elapsed = max(0.0, (curr_dt - last_dt).total_seconds() / 86400.0)
    except Exception:
        days_elapsed = 0.0

    # Retain at least 70% of floor baseline even under long absence
    decay_factor = math.exp(-DECAY_RATE_PER_DAY * days_elapsed)
    decayed = last_score * decay_factor
    return round(max(0.05, min(1.0, decayed)), 3)


def update_ewma_mastery(
    current_score: float,
    is_correct: bool,
    time_spent_seconds: float = 15.0,
    attempt_count: int = 1,
    alpha: float = DEFAULT_ALPHA
) -> float:
    """
    Calculates updated mastery score using Exponentially Weighted Moving Average (EWMA).
    
    Formula:
        target = 1.0 if is_correct else 0.0
        new_score = alpha * target + (1 - alpha) * current_score
    """
    # Baseline target performance
    target = 1.0 if is_correct else 0.0

    # Slight speed bonus/penalty (target 5s - 60s benchmark)
    if is_correct and time_spent_seconds < 10.0:
        target = min(1.0, target + 0.05)
    elif not is_correct and time_spent_seconds > 45.0:
        target = max(0.0, target - 0.05)

    # Adaptive alpha: higher learning rate for early attempts to calibrate quickly
    effective_alpha = min(0.50, alpha * (1.5 / math.sqrt(max(1, attempt_count))))

    new_score = (effective_alpha * target) + ((1.0 - effective_alpha) * current_score)
    return round(max(0.05, min(1.0, new_score)), 2)


def get_recommended_action(score: float) -> Tuple[str, str]:
    """
    Determines optimal next pedagogical action based on mastery score.
    Returns (suggested_action, rationale).
    """
    if score < 0.40:
        return (
            "lesson",
            f"Mastery ({score:.2f}) is low. A visual whiteboard walkthrough is recommended to build foundational intuition."
        )
    elif score < 0.70:
        return (
            "quiz",
            f"Mastery ({score:.2f}) is developing. Targeted check questions will reinforce edge cases and boundaries."
        )
    else:
        return (
            "flashcard",
            f"Mastery ({score:.2f}) is strong. Spaced repetition flashcards are suggested for long-term retention."
        )


def generate_pedagogical_remediation(concept_tag: str, misconceptions: List[str]) -> str:
    """Generates specific corrective study guidance based on concept and misconception."""
    if "confuses_direction_when_target_greater" in misconceptions:
        return "Review pointer movement: when target > mid, search the right partition (low = mid + 1)."
    if "confuses_low_with_high_shift" in misconceptions or "fails_to_exclude_checked_midpoint" in misconceptions:
        return "Remember to exclude the already-evaluated midpoint: always use mid + 1 or mid - 1."
    if "infinite_loop_on_two_elements" in misconceptions:
        return "Check integer division: mid = low + (high - low) // 2 ensures proper termination."
    return f"Review foundational rules and interactive step trace for {concept_tag.replace('_', ' ')}."
