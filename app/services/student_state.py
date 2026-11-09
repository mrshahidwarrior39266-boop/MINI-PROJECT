"""
Student State & Mastery Engine:
Maintains the student's epistemic state across concepts.
Uses mathematical knowledge tracing to update mastery and confidence
based on concrete assessment evidence, not self-reported sentiment.
"""
import math
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any

from app.models.student import StudentProfile, ConceptMastery, AssessmentLog


class StudentStateService:
    def __init__(self, profile: StudentProfile, repository: Optional[Any] = None):
        self.profile = profile
        self.repository = repository
        self.mastery_map: Dict[str, ConceptMastery] = {}
        self.assessment_history: List[AssessmentLog] = []

        if self.repository is not None:
            self.repository.save_profile(profile)
            self.mastery_map = self.repository.load_mastery_map(profile.student_id)
            self.assessment_history = self.repository.load_assessment_history(profile.student_id)

    def get_or_create_mastery(self, concept_id: str) -> ConceptMastery:
        """Fetch mastery record for a concept, initializing with 0 if unseen."""
        if concept_id not in self.mastery_map:
            self.mastery_map[concept_id] = ConceptMastery(concept_id=concept_id)
        return self.mastery_map[concept_id]

    def record_assessment(
        self,
        concept_id: str,
        question: str,
        student_response: str,
        score: float,
        detected_misconceptions: Optional[List[str]] = None,
        feedback: str = ""
    ) -> Tuple[ConceptMastery, AssessmentLog]:
        """
        Updates concept mastery using an evidence-based Exponential Moving Average (EMA)
        with an explicit misconception penalty.

        Math:
            alpha = 0.35 (learning rate)
            new_mastery = (1 - alpha) * old_mastery + alpha * score
            if misconceptions detected:
                new_mastery = max(0.0, new_mastery - (0.12 * count))

        Confidence increases monotonically with observation count:
            confidence = 1.0 - e^(-0.45 * attempts)
        """
        detected_misconceptions = detected_misconceptions or []
        record = self.get_or_create_mastery(concept_id)
        now = datetime.now(timezone.utc)

        # 1. Update attempt counters
        record.attempts_count += 1
        is_correct = score >= 0.75
        if is_correct:
            record.success_count += 1

        # 2. Mathematical Mastery Calculation
        alpha = 0.35  # responsiveness to new evidence
        base_update = ((1.0 - alpha) * record.mastery) + (alpha * score)

        # Misconception penalty: cognitive bugs reduce mastery immediately
        misconception_penalty = len(detected_misconceptions) * 0.12
        updated_mastery = max(0.0, min(1.0, base_update - misconception_penalty))

        record.mastery = round(updated_mastery, 4)

        # 3. Statistical Confidence Calibration
        # As student solves more problems, the system's certainty in the mastery score rises.
        record.confidence = round(1.0 - math.exp(-0.45 * record.attempts_count), 4)
        record.last_practiced = now

        # 4. Active Misconceptions State
        # If student succeeded without errors, clear old active misconceptions
        if is_correct and not detected_misconceptions:
            record.active_misconceptions = []
        else:
            # Merge new misconceptions
            existing = set(record.active_misconceptions)
            existing.update(detected_misconceptions)
            record.active_misconceptions = sorted(list(existing))

        # 5. Spaced Repetition Scheduling (Interval Growth)
        # Higher consecutive success leads to exponential days until review
        if is_correct:
            interval_days = int(math.pow(2, min(record.success_count, 5)))
        else:
            interval_days = 1  # Remediate tomorrow if failed

        record.next_review_due = now + timedelta(days=interval_days)

        # 6. Immutable Assessment Log
        log = AssessmentLog(
            id=str(uuid.uuid4()),
            student_id=self.profile.student_id,
            concept_id=concept_id,
            question_asked=question,
            student_response=student_response,
            is_correct=is_correct,
            score=score,
            detected_misconceptions=detected_misconceptions,
            evaluator_feedback=feedback,
            timestamp=now
        )
        self.assessment_history.append(log)

        if self.repository is not None:
            self.repository.save_mastery(self.profile.student_id, record)
            self.repository.save_assessment_log(log)

        return record, log
