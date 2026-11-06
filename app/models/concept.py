"""
Domain models for Educational Concepts, Knowledge Units, and Misconceptions.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class Misconception(BaseModel):
    """A known cognitive flaw or common mistake students exhibit."""
    id: str = Field(..., description="Unique key, e.g., 'confuse_assign_equals'")
    name: str = Field(..., description="Human-readable title")
    description: str = Field(..., description="Why the student gets this wrong")
    counter_example: str = Field(..., description="Code or explanation showing the contradiction")
    remediation_hint: str = Field(..., description="Targeted prompt hint for the tutor")


class Concept(BaseModel):
    """An atomic unit of knowledge in the curriculum."""
    id: str = Field(..., description="Unique ID, e.g. 'py.variables'")
    subject: str = Field(default="python", description="Domain subject")
    title: str = Field(..., description="Title of the concept")
    description: str = Field(..., description="Brief summary of the concept")
    difficulty_level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    learning_objectives: List[str] = Field(default_factory=list)
    misconceptions: List[Misconception] = Field(default_factory=list)
    prerequisites: List[str] = Field(
        default_factory=list,
        description="List of concept IDs that must be mastered before this concept"
    )


class KnowledgeChunk(BaseModel):
    """A verified factual chunk of ground-truth knowledge with provenance."""
    id: str = Field(..., description="Unique chunk hash or ID")
    concept_id: str = Field(..., description="ID of the concept this chunk explains")
    source_title: str = Field(..., description="Book, documentation, or lecture title")
    source_type: Literal["textbook", "official_doc", "academic_paper", "course_transcript"] = "textbook"
    source_author: Optional[str] = None
    source_url: Optional[str] = None
    reliability_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Provenance weight: 1.0 for official docs/standard texts, lower for unverified notes"
    )
    content: str = Field(..., description="The verified factual explanation and examples")
    citations: List[str] = Field(default_factory=list)
