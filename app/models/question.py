"""
Models for Curriculum Questions, Rubrics, Explanations, Follow-ups, and Guided Scaffolding Steps.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class QuestionMistakePattern(BaseModel):
    triggers: List[str] = Field(..., description="Keywords or patterns indicating this mistake")
    diagnosis: str = Field(..., description="Specific explanation of why this mistake is wrong")
    misconception_id: Optional[str] = Field(
        default=None,
        description="ID from the concept's misconception catalog, when one matches"
    )
    regex_triggers: List[str] = Field(
        default_factory=list,
        description="Regular expressions for mistakes that need word order or numeric pairing checks"
    )


class FollowupQuestion(BaseModel):
    prompt: str
    hint: Optional[str] = None
    canonical_answer: str
    rubric_keywords: List[str] = Field(default_factory=list)
    min_keyword_hits: int = Field(
        default=1,
        ge=1,
        description="Distinct rubric ideas required before a keyword-only follow-up passes"
    )
    required_keyword_groups: List[List[str]] = Field(
        default_factory=list,
        description="Each group is one required step; every group needs a synonym"
    )
    common_mistakes: List[QuestionMistakePattern] = Field(default_factory=list)


class ScaffoldStep(BaseModel):
    step_number: int
    prompt: str
    hint: Optional[str] = None
    expected_answer: str
    rubric_keywords: List[str] = Field(default_factory=list)
    explanation: str


class CurriculumQuestion(BaseModel):
    id: str
    concept_id: str
    prompt: str
    hint: Optional[str] = None
    canonical_answer: str
    explanation: str = Field(
        ...,
        description="Comprehensive explanation of how and why the answer works"
    )
    rubric_keywords: List[str] = Field(default_factory=list)
    min_keyword_hits: int = Field(
        default=1,
        ge=1,
        description="Distinct rubric ideas required for full credit on this question"
    )
    required_keyword_groups: List[List[str]] = Field(
        default_factory=list,
        description="Each inner list is one idea; at least one synonym from every idea must appear"
    )
    common_mistakes: List[QuestionMistakePattern] = Field(default_factory=list)
    followup: Optional[FollowupQuestion] = None
    scaffold_steps: List[ScaffoldStep] = Field(
        default_factory=list,
        description="Atomic micro-steps to guide the student line-by-line if they struggle repeatedly"
    )
