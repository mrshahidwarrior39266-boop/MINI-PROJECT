"""
Data models for Dense Semantic RAG (Retrieval-Augmented Generation).
"""
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

from app.models.concept import KnowledgeChunk


class DocumentChunk(BaseModel):
    """A semantic chunk derived from an ingested document (Markdown or PDF)."""
    id: str = Field(..., description="Unique chunk ID e.g. 'doc_py_intro_chunk_001'")
    source: str = Field(..., description="Source filename or document title")
    heading_path: List[str] = Field(default_factory=list, description="Breadcrumb heading hierarchy")
    heading_level: int = Field(default=1, description="Markdown heading depth: 1 for #, 2 for ##, etc.")
    content: str = Field(..., description="Logical text block for this section")
    word_count: int = Field(default=0, description="Word count of chunk content")
    page_number: Optional[int] = Field(default=None, description="Page number if extracted from PDF")
    concept_id: Optional[str] = Field(default=None, description="Curriculum concept ID if auto-linked")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary file and chunk metadata")

    def to_knowledge_chunk(self, fallback_concept_id: str = "py.variables") -> KnowledgeChunk:
        """Convert document chunk into an authoritative KnowledgeChunk for RAG retrieval."""
        cid = self.concept_id or fallback_concept_id
        heading_title = " > ".join(self.heading_path) if self.heading_path else self.source
        return KnowledgeChunk(
            id=self.id,
            concept_id=cid,
            source_title=f"{self.source}: {heading_title}",
            source_type="textbook",
            reliability_score=0.95,
            content=self.content,
            citations=[f"{self.source} - {' / '.join(self.heading_path)}"] if self.heading_path else [self.source]
        )


class ConceptLinkageResult(BaseModel):
    """Result of an LLM extraction pass that maps an ingested chunk to the curriculum DAG."""
    chunk_id: str = Field(..., description="ID of the chunk being evaluated")
    primary_concept_id: Optional[str] = Field(
        default=None,
        description="ID of closest curriculum concept from DAG (e.g. 'py.variables')"
    )
    secondary_concept_ids: List[str] = Field(
        default_factory=list,
        description="IDs of related or secondary curriculum concepts"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of the concept mapping in [0.0, 1.0]"
    )
    reasoning: str = Field(default="", description="Pedagogical rationale for this linkage")
    key_takeaways: List[str] = Field(default_factory=list, description="Core educational takeaways")
    detected_misconceptions: List[str] = Field(
        default_factory=list,
        description="Misconceptions explicitly explained or warned about in the chunk"
    )


class IngestionSummary(BaseModel):
    """Summary report of a document ingestion run."""
    source_file: str
    format: Literal["markdown", "pdf", "text"]
    total_chunks: int = 0
    linked_chunks: int = 0
    unlinked_chunks: int = 0
    heading_hierarchy: List[str] = Field(default_factory=list)
    total_words: int = 0


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
