"""
Spaced Repetition & Memory Decay Engine:
Models cognitive retention using an exponential Ebbinghaus forgetting curve.
Calculates memory stability growth with repeated successful practice and identifies
concepts requiring spaced review before memory traces fade.
"""
from datetime import datetime, timezone
import math
from typing import Dict, List, Tuple, Optional

from app.models.student import ConceptMastery


class SpacedRepetitionEngine:
    """Calculates time-decayed mastery and ranks concepts for spaced review."""

    def __init__(
        self,
        base_stability_days: float = 2.0,
        stability_growth_factor: float = 0.6,
        retention_threshold: float = 0.70,
    ):
        self.base_stability_days = base_stability_days
        self.stability_growth_factor = stability_growth_factor
        self.retention_threshold = retention_threshold

    def calculate_stability(self, mastery: ConceptMastery) -> float:
        """
        Memory stability S in days: How long retention remains high.
        Grows with each successful practice attempt.
        """
        successes = max(0, mastery.success_count)
        return self.base_stability_days * (1.0 + self.stability_growth_factor * successes)

    def calculate_decayed_mastery(
        self,
        mastery: ConceptMastery,
        current_time: Optional[datetime] = None,
        simulated_days_elapsed: Optional[float] = None,
    ) -> float:
        """
        Calculate effective mastery: M_eff = M_0 * exp(-delta_t / S).
        Supports live timestamp calculation or explicit simulated days elapsed.
        """
        if mastery.mastery <= 0.0:
            return 0.0

        if simulated_days_elapsed is not None:
            days_elapsed = max(0.0, simulated_days_elapsed)
        elif getattr(mastery, "last_practiced", None) or getattr(mastery, "last_practiced_at", None):
            last_ts = getattr(mastery, "last_practiced", None) or getattr(mastery, "last_practiced_at", None)
            now = current_time or datetime.now(timezone.utc)
            delta = now - last_ts
            days_elapsed = max(0.0, delta.total_seconds() / 86400.0)
        else:
            # Never practiced or no timestamp recorded yet
            days_elapsed = 0.0

        stability = self.calculate_stability(mastery)
        retention_rate = math.exp(-days_elapsed / stability)
        effective = mastery.mastery * retention_rate
        return round(max(0.0, min(1.0, effective)), 4)

    def is_due_for_review(
        self,
        mastery: ConceptMastery,
        current_time: Optional[datetime] = None,
        simulated_days_elapsed: Optional[float] = None,
    ) -> bool:
        """
        A concept is due for review if:
        1. It has active unresolved cognitive misconceptions, OR
        2. It was previously learned (mastery >= threshold) but its effective retention
           has dropped below the threshold, OR
        3. The elapsed time exceeds its current memory stability half-life.
        """
        if mastery.attempts_count == 0:
            return False

        if mastery.active_misconceptions:
            return True

        decayed = self.calculate_decayed_mastery(
            mastery,
            current_time=current_time,
            simulated_days_elapsed=simulated_days_elapsed,
        )

        if mastery.mastery >= self.retention_threshold and decayed < self.retention_threshold:
            return True

        # Check stability elapsed time
        if simulated_days_elapsed is not None:
            days = simulated_days_elapsed
        elif mastery.last_practiced_at:
            now = current_time or datetime.now(timezone.utc)
            days = max(0.0, (now - mastery.last_practiced_at).total_seconds() / 86400.0)
        else:
            days = 0.0

        stability = self.calculate_stability(mastery)
        return days >= stability

    def rank_concepts_for_review(
        self,
        mastery_map: Dict[str, ConceptMastery],
        current_time: Optional[datetime] = None,
        simulated_days_map: Optional[Dict[str, float]] = None,
    ) -> List[Tuple[str, float]]:
        """
        Rank candidate review concepts by review urgency.
        Returns list of (concept_id, effective_decayed_mastery) sorted by lowest score first.
        """
        candidates: List[Tuple[str, float]] = []

        for cid, m in mastery_map.items():
            if m.attempts_count == 0:
                continue

            sim_days = simulated_days_map.get(cid) if simulated_days_map else None
            decayed = self.calculate_decayed_mastery(
                m, current_time=current_time, simulated_days_elapsed=sim_days
            )

            # Prioritize if misconceptions are active or decayed
            if m.active_misconceptions or self.is_due_for_review(
                m, current_time=current_time, simulated_days_elapsed=sim_days
            ):
                urgency_score = decayed - (0.3 if m.active_misconceptions else 0.0)
                candidates.append((cid, urgency_score))

        # Sort by lowest urgency score first (highest urgency)
        candidates.sort(key=lambda x: x[1])
        return candidates
