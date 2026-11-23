"""
Automated Unit and Integration Tests for Dense Semantic RAG.
"""
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from app.services.embedding_service import (
    DeterministicSemanticEmbedding,
    cosine_similarity,
    normalize_vector,
)
from app.services.semantic_rag import SemanticRAGService
from app.services.student_repository import StudentRepository

DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "data"
KNOWLEDGE_FILE = DATA_DIR / "python_knowledge.json"


def test_vector_normalization_and_cosine_similarity():
    # Unit normalization
    v = [3.0, 4.0]
    norm_v = normalize_vector(v)
    assert abs(norm_v[0] - 0.6) < 1e-6
    assert abs(norm_v[1] - 0.8) < 1e-6

    # Identical vectors -> similarity = 1.0
    assert abs(cosine_similarity(norm_v, norm_v) - 1.0) < 1e-6

    # Orthogonal vectors -> similarity = 0.0
    v_ortho = [-0.8, 0.6]
    assert abs(cosine_similarity(norm_v, v_ortho)) < 1e-6

    # Opposite vectors -> similarity = -1.0
    v_opp = [-0.6, -0.8]
    assert abs(cosine_similarity(norm_v, v_opp) - (-1.0)) < 1e-6

    # Zero vector safety
    v_zero = [0.0, 0.0]
    assert cosine_similarity(norm_v, v_zero) == 0.0


def test_deterministic_semantic_embedding_invariants():
    embedder = DeterministicSemanticEmbedding(dimension=128)
    assert embedder.dimension == 128
    assert embedder.provider_name == "deterministic_semantic"

    # Determinism: same input produces identical vector
    v1 = embedder.embed_text("x = 10 creates a name tag in memory")
    v2 = embedder.embed_text("x = 10 creates a name tag in memory")
    assert v1 == v2
    assert len(v1) == 128

    # Vector has non-zero length and is unit-normalized
    norm = sum(x * x for x in v1)
    assert abs(norm - 1.0) < 1e-5

    # Empty string returns zero vector
    v_empty = embedder.embed_text("")
    assert all(x == 0.0 for x in v_empty)


def test_dense_rag_indexes_all_curriculum_concepts():
    rag = SemanticRAGService(KNOWLEDGE_FILE)
    assert len(rag.chunks_by_id) >= 8
    assert len(rag.chunks_by_concept) >= 8
    assert "py.variables" in rag.chunks_by_concept
    assert "py.for_loops" in rag.chunks_by_concept
    assert "py.functions" in rag.chunks_by_concept


def test_concept_scoped_retrieval_respects_filter():
    rag = SemanticRAGService(KNOWLEDGE_FILE)
    res = rag.retrieve(
        query="for x in sequence iterate over items",
        concept_id="py.variables",
        top_k=3,
    )
    # Even if query mentions loops, filter enforces py.variables
    assert all(m.chunk.concept_id == "py.variables" for m in res.matches)
    assert res.concept_filter == "py.variables"


def test_semantic_relevance_ranking_without_filter():
    rag = SemanticRAGService(KNOWLEDGE_FILE)

    # 1. Variables query ranks py.variables at top
    res_var = rag.retrieve("how does variable assignment x = 5 store values in memory?")
    assert len(res_var.matches) > 0
    top_var = res_var.matches[0]
    assert top_var.chunk.concept_id == "py.variables"
    assert top_var.similarity_score > 0.35

    # 2. While loop break query ranks py.while_loops at top
    res_while = rag.retrieve("while condition is true run loop until break statement")
    assert len(res_while.matches) > 0
    top_while = res_while.matches[0]
    assert top_while.chunk.concept_id == "py.while_loops"
    assert top_while.similarity_score > 0.35

    # 3. Lists indexing query ranks py.lists_sequences at top
    res_list = rag.retrieve("accessing list elements using zero-based index fruits[0]")
    assert len(res_list.matches) > 0
    top_list = res_list.matches[0]
    assert top_list.chunk.concept_id == "py.lists_sequences"
    assert top_list.similarity_score > 0.40


def test_sqlite_embedding_persistence_cache():
    with TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_rag_cache.db"
        repo = StudentRepository(db_path)

        # First load: computes and caches embeddings in SQLite
        rag1 = SemanticRAGService(KNOWLEDGE_FILE, repository=repo)
        assert len(rag1.chunk_vectors) >= 8

        # Verify rows exist in SQLite table
        cached_data = repo.load_chunk_embeddings(provider_name=rag1.embedding_service.provider_name)
        assert len(cached_data) >= 8
        for cid, data in cached_data.items():
            assert data["dimension"] == rag1.embedding_service.dimension
            assert len(data["embedding"]) == rag1.embedding_service.dimension

        # Second load: loads directly from SQLite cache
        rag2 = SemanticRAGService(KNOWLEDGE_FILE, repository=repo)
        for cid, vec1 in rag1.chunk_vectors.items():
            vec2 = rag2.chunk_vectors.get(cid)
            assert vec2 is not None
            assert vec1 == vec2


def test_rag_context_formatting_for_prompts():
    rag = SemanticRAGService(KNOWLEDGE_FILE)
    res = rag.retrieve("meaning of x = x + 1", concept_id="py.variables", top_k=2)
    formatted = rag.format_context_for_prompt(res.matches)

    assert "Verified Subject Ground Truth" in formatted
    assert "Reliability Score:" in formatted
    assert "Semantic Match:" in formatted
    assert "Official Python 3 Documentation" in formatted
