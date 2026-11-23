"""
Unit and integration tests for Milestone 3:
- Document Ingestion & Heading-based Semantic Chunking (Markdown & PDF)
- LLM Concept Auto-Linker
- pgvector Schema & Vector Store (SQLite & PGVectorStore)
- Mandatory chunk ID citation enforcement in LLM Evaluator
"""
from pathlib import Path
import pytest

from app.models.concept import KnowledgeChunk
from app.models.rag import DocumentChunk
from app.models.evaluator import LLMEvaluationRequest, LLMEvaluationResponse
from app.services.concept_graph import ConceptGraphService
from app.services.document_ingestion import DocumentIngestionService
from app.services.concept_linker import ConceptLinkerService
from app.services.vector_store import (
    create_vector_store,
    SQLiteVectorStore,
    PGVectorStore,
)
from app.services.semantic_rag import SemanticRAGService
from app.services.student_repository import StudentRepository
from app.services.llm_client import MockLLMClient
from app.services.llm_evaluator import LLMEvaluator

ROOT = Path(__file__).resolve().parent.parent
CONCEPTS_FILE = ROOT / "app" / "data" / "python_concepts.json"
KNOWLEDGE_FILE = ROOT / "app" / "data" / "python_knowledge.json"
SAMPLE_DOCS_DIR = ROOT / "app" / "data" / "sample_documents"
SAMPLE_MD = SAMPLE_DOCS_DIR / "control_flow_and_data_structures.md"
SAMPLE_PDF = SAMPLE_DOCS_DIR / "python_functions_reference.pdf"


def test_markdown_semantic_heading_chunking():
    """Test that markdown is split strictly by headings into logical semantic units."""
    service = DocumentIngestionService(min_chunk_words=5)
    md_text = """# Chapter 1: Introduction

This is the general introduction to the programming language and runtime.

## Variables and Memory Binding

In Python, variables are names referencing objects in memory.
When you write x = 5, Python binds the name x to the integer 5.

```python
# A comment with a hash that is NOT a markdown heading
def dummy():
    pass
```

### Swapping References Safely

To swap x and y without losing data, use an intermediate temporary variable.
"""
    chunks = service.ingest_markdown_text(md_text, source_name="test_textbook.md")
    assert len(chunks) == 3

    # Chunk 1: Top-level Introduction
    assert chunks[0].heading_path == ["Chapter 1: Introduction"]
    assert "general introduction" in chunks[0].content

    # Chunk 2: Variables section (code block preserved, comment # ignored)
    assert chunks[1].heading_path == [
        "Chapter 1: Introduction",
        "Variables and Memory Binding",
    ]
    assert "def dummy():" in chunks[1].content
    assert "binds the name x" in chunks[1].content

    # Chunk 3: Sub-section
    assert chunks[2].heading_path == [
        "Chapter 1: Introduction",
        "Variables and Memory Binding",
        "Swapping References Safely",
    ]
    assert "intermediate temporary variable" in chunks[2].content


def test_markdown_file_ingestion_summary():
    """Test reading from disk and generating summary statistics."""
    service = DocumentIngestionService(min_chunk_words=10)
    chunks, summary = service.ingest_file(SAMPLE_MD)
    assert len(chunks) >= 4
    assert summary.format == "markdown"
    assert summary.total_words > 150
    assert len(summary.heading_hierarchy) >= 4


def test_pdf_ingestion():
    """Test PDF text extraction and chunking with page number tracking."""
    service = DocumentIngestionService(min_chunk_words=10)
    chunks, summary = service.ingest_file(SAMPLE_PDF)
    assert len(chunks) >= 1
    assert summary.format == "pdf"
    assert chunks[0].page_number == 1
    assert "FUNCTION DEFINITIONS" in chunks[0].content


def test_concept_linker_deterministic_fallback():
    """Test heuristic keyword density concept mapper for offline resilience."""
    graph = ConceptGraphService(CONCEPTS_FILE)
    linker = ConceptLinkerService(concepts_catalog=graph.concepts)

    chunk = DocumentChunk(
        id="chunk_test_01",
        source="notes.md",
        heading_path=["Iteration", "While Loops"],
        content="While loops repeatedly execute until a sentinel condition becomes false. Always update your counter.",
    )
    result = linker.link_chunk(chunk)
    assert result.primary_concept_id == "py.while_loops"
    assert result.confidence >= 0.70
    assert chunk.concept_id == "py.while_loops"


def test_vector_store_sqlite_operations(tmp_path):
    """Test vector storage, BLOB packing, and cosine similarity ranking in SQLite."""
    db_file = tmp_path / "test_vectors.db"
    store = SQLiteVectorStore(db_path=db_file)

    chunk1 = KnowledgeChunk(
        id="c1",
        concept_id="py.variables",
        source_title="Book 1",
        reliability_score=1.0,
        content="Variables store values.",
        citations=["cite 1"],
    )
    chunk2 = KnowledgeChunk(
        id="c2",
        concept_id="py.for_loops",
        source_title="Book 2",
        reliability_score=1.0,
        content="For loops iterate over sequences.",
        citations=["cite 2"],
    )

    # 4-dimensional mock embeddings
    v1 = [1.0, 0.0, 0.0, 0.0]
    v2 = [0.0, 1.0, 0.0, 0.0]

    store.add_chunks([chunk1, chunk2], [v1, v2])
    assert store.count() == 2

    # Query pointing towards v1
    query = [0.9, 0.1, 0.0, 0.0]
    matches = store.similarity_search(query, top_k=1)
    assert len(matches) == 1
    best_chunk, score = matches[0]
    assert best_chunk.id == "c1"
    assert score > 0.85

    # Concept scoped query
    matches_scoped = store.similarity_search(query, top_k=2, concept_id="py.for_loops")
    assert len(matches_scoped) == 1
    assert matches_scoped[0][0].id == "c2"


def test_pgvector_ddl_generation():
    """Test PostgreSQL pgvector schema generation syntax."""
    ddl = PGVectorStore.get_schema_ddl(dimension=1536, table_name="test_curriculum")
    assert "CREATE EXTENSION IF NOT EXISTS vector;" in ddl
    assert "vector(1536)" in ddl
    assert "USING hnsw (embedding vector_cosine_ops)" in ddl
    assert "CREATE INDEX IF NOT EXISTS idx_test_curriculum_concept" in ddl


def test_source_citation_enforcement_in_evaluator():
    """Test that LLMEvaluator strictly populates and validates chunk ID citations."""
    rag_service = SemanticRAGService(KNOWLEDGE_FILE)
    evaluator = LLMEvaluator(rag_service=rag_service)

    req = LLMEvaluationRequest(
        concept_id="py.variables",
        concept_title="Variable Assignment",
        question="What does x = 10 do?",
        student_response="It assigns 10 to x.",
        misconception_catalog=[],
    )
    resp = evaluator.evaluate(req)
    assert isinstance(resp.cited_chunk_ids, list)
    assert len(resp.cited_chunk_ids) > 0
    # Every cited chunk must exist in knowledge base
    for cid in resp.cited_chunk_ids:
        assert cid in rag_service.chunks_by_id


def test_semantic_rag_dynamic_ingest_document():
    """Test end-to-end document ingestion through SemanticRAGService."""
    rag_service = SemanticRAGService(KNOWLEDGE_FILE)
    initial_count = len(rag_service.chunks_by_id)

    graph = ConceptGraphService(CONCEPTS_FILE)
    linker = ConceptLinkerService(concepts_catalog=graph.concepts)

    summary = rag_service.ingest_document(SAMPLE_MD, linker=linker)
    assert summary.total_chunks > 0
    assert len(rag_service.chunks_by_id) == initial_count + summary.total_chunks

    # Verify that the newly ingested chunks are immediately retrievable
    retrieval = rag_service.retrieve("while loops sentinel termination", top_k=3)
    chunk_ids = [m.chunk.id for m in retrieval.matches]
    assert any("control_flow_and_data_structures" in cid for cid in chunk_ids)


def test_semantic_rag_ingest_with_repository_persists_embeddings(tmp_path):
    """Ingestion must use the repository's keyword-only embedding schema."""
    repo = StudentRepository(tmp_path / "rag_records.db")
    rag_service = SemanticRAGService(KNOWLEDGE_FILE, repository=repo)
    graph = ConceptGraphService(CONCEPTS_FILE)
    linker = ConceptLinkerService(concepts_catalog=graph.concepts)

    doc_path = tmp_path / "sentinel_notes.md"
    doc_path.write_text(
        "# Sentinel Flags\n\nA sentinel flag tells a while loop when to stop. "
        "Update the flag and use break to terminate the loop safely.\n",
        encoding="utf-8",
    )

    before_ids = set(rag_service.chunks_by_id)
    summary = rag_service.ingest_document(doc_path, linker=linker)
    new_ids = set(rag_service.chunks_by_id) - before_ids
    assert summary.total_chunks > 0
    assert new_ids

    # This is the regression: the old positional call raised TypeError and
    # aborted ingestion after the in-memory chunks had already been added.
    embeddings = repo.load_chunk_embeddings()
    assert new_ids <= set(embeddings)
