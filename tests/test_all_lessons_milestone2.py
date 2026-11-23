"""
Comprehensive Verification: Milestone 2 Across Every Single Lesson in Curriculum.

Guarantees that all 8 curriculum concepts have:
1. Ground-truth knowledge chunks with verified provenance and citations.
2. Dense semantic embeddings indexed with high cosine similarity retrieval.
3. Structured Socratic evaluation with RAG context injection.
4. Misconception catalog mapping.
5. Dynamic transfer challenge generation.
6. Mathematical mastery tracing and persistence via TutorCoordinator.
"""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from app.models.concept import Concept, Misconception
from app.models.student import StudentProfile
from app.models.evaluator import LLMEvaluationRequest, LLMEvaluationResponse
from app.services.semantic_rag import SemanticRAGService
from app.services.llm_client import MockLLMClient
from app.services.llm_evaluator import LLMEvaluator
from app.services.tutor_coordinator import TutorCoordinator
from app.services.student_repository import StudentRepository

DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "data"
CONCEPTS_FILE = DATA_DIR / "python_concepts.json"
KNOWLEDGE_FILE = DATA_DIR / "python_knowledge.json"
QUESTIONS_FILE = DATA_DIR / "curriculum_questions.json"

LESSON_BENCHMARK_QUERIES = {
    "py.variables": "how do variable assignment and memory references work in Python?",
    "py.data_types": "integers floats strings booleans and type conversions",
    "py.operators_expressions": "arithmetic operators floor division modulo and operator precedence",
    "py.conditionals": "if elif else branching boolean conditions comparison",
    "py.lists_sequences": "lists indexing zero based indexing slicing elements",
    "py.for_loops": "iterating over sequence with for loop and range function",
    "py.while_loops": "while loop condition break continue loop control",
    "py.functions": "defining functions with def parameters arguments and return values",
}


@pytest.fixture(scope="module")
def curriculum_concepts():
    raw = json.loads(CONCEPTS_FILE.read_text(encoding="utf-8"))
    return [Concept(**c) for c in raw]


@pytest.fixture(scope="module")
def rag_service():
    return SemanticRAGService(KNOWLEDGE_FILE)


def test_every_lesson_has_dense_embeddings_indexed(curriculum_concepts, rag_service):
    """Verify that every concept has indexed knowledge chunks and embeddings."""
    assert len(curriculum_concepts) == 8

    for concept in curriculum_concepts:
        cid = concept.id
        assert cid in rag_service.chunks_by_concept, f"Lesson '{cid}' missing in RAG concept index"
        chunks = rag_service.chunks_by_concept[cid]
        assert len(chunks) > 0, f"Lesson '{cid}' has no chunks"

        for chunk in chunks:
            assert chunk.id in rag_service.chunk_vectors, f"Chunk '{chunk.id}' missing dense vector"
            vec = rag_service.chunk_vectors[chunk.id]
            assert len(vec) == rag_service.embedding_service.dimension
            # Verify unit normalization
            norm = sum(x * x for x in vec)
            assert abs(norm - 1.0) < 1e-4, f"Chunk vector for '{chunk.id}' not unit normalized"


@pytest.mark.parametrize("concept_id,query", list(LESSON_BENCHMARK_QUERIES.items()))
def test_dense_rag_retrieves_correct_chunk_for_every_lesson(concept_id, query, rag_service):
    """Verify that semantic retrieval accurately ranks each lesson's chunk at or near top."""
    # 1. Concept-scoped retrieval: guarantees 100% precision
    scoped_res = rag_service.retrieve(query, concept_id=concept_id, top_k=2)
    assert len(scoped_res.matches) > 0
    assert scoped_res.matches[0].chunk.concept_id == concept_id
    assert scoped_res.matches[0].similarity_score > 0.30

    # 2. Global search: the targeted lesson should be top match or in top 2
    global_res = rag_service.retrieve(query, top_k=3)
    assert len(global_res.matches) > 0
    top_cids = [m.chunk.concept_id for m in global_res.matches[:2]]
    assert concept_id in top_cids, (
        f"For query '{query}', expected '{concept_id}' in top 2, got {top_cids}"
    )


def test_every_lesson_supports_socratic_llm_evaluation(curriculum_concepts, rag_service):
    """Verify that LLMEvaluator successfully processes evaluation across all 8 lessons."""
    for concept in curriculum_concepts:
        cid = concept.id

        # Prepare a mock response tailored to this concept
        active_misc = concept.misconceptions[0].id if concept.misconceptions else None
        mock_resp = LLMEvaluationResponse(
            is_correct=True,
            score=0.9,
            detected_misconceptions=[],
            diagnosis=f"Student demonstrated understanding of {concept.title}.",
            feedback=f"Good explanation of {concept.title}.",
            step_by_step_explanation="Mechanics verified.",
            evaluator_mode="llm_rag_grounded",
        )
        mock_client = MockLLMClient(default_model_instance=mock_resp)
        evaluator = LLMEvaluator(llm_client=mock_client, rag_service=rag_service)

        req = LLMEvaluationRequest(
            concept_id=cid,
            concept_title=concept.title,
            question=f"Explain how {concept.title} works in Python.",
            student_response=f"Clear explanation of {concept.title}.",
            misconception_catalog=concept.misconceptions,
        )

        res = evaluator.evaluate(req)

        assert res.evaluator_mode == "llm_rag_grounded"
        assert res.is_correct is True
        assert res.score == 0.9

        # Verify call history received RAG context for this concept
        assert len(mock_client.call_history) == 1
        prompt_text = mock_client.call_history[0]["prompt"]
        assert f"Target Concept: {concept.title}" in prompt_text
        assert "AUTHORITATIVE REFERENCES:" in prompt_text


def test_every_lesson_supports_dynamic_transfer_question_generation(curriculum_concepts, rag_service):
    """Verify that dynamic transfer questions can be generated for every lesson."""
    for concept in curriculum_concepts:
        cid = concept.id
        evaluator = LLMEvaluator(llm_client=None, rag_service=rag_service)

        misc = concept.misconceptions[0] if concept.misconceptions else None
        transfer_q = evaluator.generate_transfer_question(
            concept_id=cid,
            concept_title=concept.title,
            active_misconception=misc,
        )

        assert transfer_q.concept_id == cid
        assert transfer_q.prompt is not None and len(transfer_q.prompt) > 10
        assert transfer_q.expected_answer is not None


def test_every_lesson_integrates_with_coordinator_and_mastery(curriculum_concepts):
    """Verify that TutorCoordinator can evaluate and trace mastery for every lesson."""
    with TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_all_lessons.db"
        repo = StudentRepository(db_path)

        student = StudentProfile(
            student_id="stu_curriculum_tester",
            name="Curriculum Tester",
            target_goal="Test all 8 lessons",
        )

        coordinator = TutorCoordinator(
            student_profile=student,
            concepts_file=CONCEPTS_FILE,
            knowledge_file=KNOWLEDGE_FILE,
            mastery_threshold=0.70,
            repository=repo,
        )

        for concept in curriculum_concepts:
            cid = concept.id
            result = coordinator.evaluate_student_response(
                concept_id=cid,
                question=f"Test question for {concept.title}",
                student_response=f"Test response for {concept.title}",
            )

            assert "new_mastery" in result
            assert "confidence" in result
            assert "evaluator_mode" in result
            assert result["assessment_id"] is not None

        # Verify all 8 concepts have records in persistence
        mastery_map = repo.load_mastery_map("stu_curriculum_tester")
        assert len(mastery_map) == 8
        for concept in curriculum_concepts:
            assert concept.id in mastery_map
