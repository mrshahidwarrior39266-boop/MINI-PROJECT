"""
Curriculum models representing the Learning Frontier, Dependency Hierarchy, and Session Plans.
"""
from enum import Enum
from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field


class ConceptState(str, Enum):
    LOCKED = "LOCKED"             # Prerequisites not yet satisfied
    READY = "READY"               # Eligible to be taught (all prereqs >= threshold)
    IN_PROGRESS = "IN_PROGRESS"   # Attempted, but not yet mastered
    MASTERED = "MASTERED"         # Proven mastery >= threshold
    DUE_FOR_REVIEW = "DUE_FOR_REVIEW" # Decayed or due via spaced repetition


class LearningFrontier(BaseModel):
    """
    The current active learning boundary for a student.
    Separates what the student knows, what they are ready to learn next, and what is blocked.
    """
    ready: List[str] = Field(
        default_factory=list,
        description="Concepts where all prerequisites are mastered (>= threshold) but target is unmastered"
    )
    in_progress: List[str] = Field(
        default_factory=list,
        description="Concepts partially attempted with pending mastery or active misconceptions"
    )
    due_for_review: List[str] = Field(
        default_factory=list,
        description="Previously mastered concepts needing spaced repetition reinforcement"
    )
    locked: List[str] = Field(
        default_factory=list,
        description="Advanced concepts currently blocked by missing prerequisites"
    )
    mastered: List[str] = Field(
        default_factory=list,
        description="Concepts fully mastered by the student"
    )


class SessionGoal(BaseModel):
    """Target objective for the current tutoring interaction."""
    target_concept_id: str
    target_concept_title: str
    action_type: str  # "INTRODUCE", "PRACTICE", "REMEDIATE", "REVISE"
    active_misconceptions: List[str] = Field(default_factory=list)
    prerequisites_verified: bool = True


class SynthesisChallenge(BaseModel):
    """A multi-concept capstone challenge testing the synthesis of 2+ curriculum concepts."""
    id: str = Field(..., description="Unique synthesis challenge ID, e.g. 'syn_loops_lists_01'")
    title: str = Field(..., description="Title of the challenge")
    required_concept_ids: List[str] = Field(
        ...,
        description="List of concept IDs that must be combined to solve this problem"
    )
    prompt: str = Field(..., description="Problem statement presented to the learner")
    hint: Optional[str] = Field(default=None, description="Hint guiding multi-concept coordination")
    canonical_answer: str = Field(..., description="Reference implementation or explanation")
    rubric_keywords: List[str] = Field(default_factory=list)
    explanation: str = Field(..., description="Comprehensive pedagogical breakdown")


class PlannedExercise(BaseModel):
    """A single scheduled activity within a personalized daily session plan."""
    item_index: int = Field(..., description="Position in daily schedule (1-indexed)")
    bucket: Literal["REVIEW", "FRONTIER", "SYNTHESIS"] = Field(
        ...,
        description="Curriculum partition: 30% Review, 60% Frontier Learning, or 10% Synthesis"
    )
    concept_id: str = Field(..., description="Target primary concept ID or 'synthesis'")
    concept_title: str = Field(..., description="Human-readable concept title")
    exercise_prompt: str = Field(..., description="Question or challenge prompt")
    hint: Optional[str] = None
    canonical_answer: Optional[str] = None
    estimated_minutes: int = Field(default=3, description="Estimated time to complete")
    rationale: str = Field(..., description="Why this exercise was scheduled for today")
    decay_score: Optional[float] = Field(default=None, description="Current effective mastery if under review")


class DailySessionPlan(BaseModel):
    """
    Personalized Daily Session Plan generated from DAG traversal & spaced repetition.
    Strictly partitions learning into:
    - 30% Review (spaced repetition of decaying concepts)
    - 60% Frontier Learning (introducing and practicing next unlocked concepts)
    - 10% Synthesis / Challenge problem (multi-concept capstone)
    """
    session_id: str
    student_id: str
    student_name: str
    generated_at: str
    target_total_items: int = 10
    review_items: List[PlannedExercise] = Field(default_factory=list)
    frontier_items: List[PlannedExercise] = Field(default_factory=list)
    synthesis_items: List[PlannedExercise] = Field(default_factory=list)
    all_scheduled_items: List[PlannedExercise] = Field(default_factory=list)
    frontier_summary: LearningFrontier
    estimated_total_minutes: int = 0
    ratio_summary: str = "30% Review | 60% Frontier Learning | 10% Synthesis Challenge"

