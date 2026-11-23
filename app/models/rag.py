"""
Data models for Dense Semantic RAG (Retrieval-Augmented Generation).
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from app.models.concept import KnowledgeChunk


class ScoredChunk(BaseModel):
    """A retrieved knowledge chunk paired with its relevance score."""
    chunk: KnowledgeChunk
    similarity_score: float = Field(
        ...,
        description="Dense vector cosine similarity or hybrid match score in [0.0, 1.0]"
    )
    reliability_weighted_score: float = Field(
        ...,
        description="Combined score: similarity_score * chunk.reliability_score"
    )
    retrieval_method: Literal["dense_vector", "hybrid", "lexical"] = "dense_vector"


class RetrievalQuery(BaseModel):
    """Query parameters for knowledge retrieval."""
    query_text: str = Field(..., description="Student response, concept question, or search query")
    concept_id: Optional[str] = Field(
        default=None,
        description="Optional concept ID to scope the search to a specific curriculum node"
    )
    top_k: int = Field(default=3, ge=1, le=20, description="Max number of chunks to return")
    min_similarity: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum similarity threshold")


class RetrievalResult(BaseModel):
    """Result of a RAG retrieval operation."""
    query: str
    concept_filter: Optional[str] = None
    matches: List[ScoredChunk] = Field(default_factory=list)
    retrieval_time_ms: float = 0.0
    embedding_dimension: int = 0
