"""
Curriculum models representing the Learning Frontier, Dependency Hierarchy, and Session Plans.
"""
from enum import Enum
from typing import List, Dict, Optional
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
