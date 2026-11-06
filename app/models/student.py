"""
Models representing the Student's Epistemic State, Profile, and Evidence Logs.
"""
from datetime import datetime, timezone
from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field


class StudentProfile(BaseModel):
    """Static and behavioral preferences of the learner."""
    student_id: str = Field(..., description="Unique user ID")
    name: str = Field(default="Student")
    target_goal: str = Field(
        default="Master basic Python for programming",
        description="User's stated educational goal"
    )
    explanation_preference: Literal["analogy_heavy", "technical_concise", "visual_step_by_step"] = (
        "analogy_heavy"
    )
    pace_rate: float = Field(default=1.0, ge=0.5, le=2.0, description="Multiplier for difficulty and review frequency")


class ConceptMastery(BaseModel):
    """Dynamic epistemic state of a student for a single concept."""
    concept_id: str
    mastery: float = Field(default=0.0, ge=0.0, le=1.0, description="Estimated probability of mastery [0.0, 1.0]")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Statistical confidence in the estimate")
    attempts_count: int = Field(default=0, ge=0)
    success_count: int = Field(default=0, ge=0)
    last_practiced: Optional[datetime] = None
    next_review_due: Optional[datetime] = None
    active_misconceptions: List[str] = Field(
        default_factory=list,
        description="IDs of currently observed misconceptions that need remediation"
    )


class AssessmentLog(BaseModel):
    """Immutable audit log of an assessment interaction (the proof of learning)."""
    id: str
    student_id: str
    concept_id: str
    question_asked: str
    student_response: str
    is_correct: bool
    score: float = Field(..., ge=0.0, le=1.0, description="Rubric score 0.0 to 1.0")
    detected_misconceptions: List[str] = Field(default_factory=list)
    evaluator_feedback: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
