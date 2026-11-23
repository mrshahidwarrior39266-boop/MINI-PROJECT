"""
Automated Unit and Integration Tests for LLM Socratic Evaluator & Socratic Agent.
"""
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from app.models.concept import Misconception
from app.models.student import StudentProfile
from app.models.evaluator import (
    LLMEvaluationRequest,
    LLMEvaluationResponse,
    GeneratedTransferQuestion,
)
from app.services.llm_client import MockLLMClient
from app.services.llm_evaluator import LLMEvaluator
from app.services.semantic_rag import SemanticRAGService
from app.services.tutor_coordinator import TutorCoordinator
from app.services.student_repository import StudentRepository

DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "data"
CONCEPTS_FILE = DATA_DIR / "python_concepts.json"
KNOWLEDGE_FILE = DATA_DIR / "python_knowledge.json"


@pytest.fixture
def sample_misconceptions():
    return [
        Misconception(
            id="confuse_assign_equals",
            name="Confusing Assignment with Algebraic Equality",
            description="Treats = as algebraic equality rather than imperative assignment.",
            counter_example="x = x + 1 is valid in Python.",
            remediation_hint="Explain right side evaluates first.",
        ),
        Misconception(
            id="simultaneous_assignment_confusion",
            name="Variable Overwrite Order Error",
            description="Overwrites x before saving to temporary variable.",
            counter_example="x = y overwrites x before saving it.",
            remediation_hint="Save x into temp first.",
        ),
    ]


def test_mock_llm_structured_evaluation_with_rag(sample_misconceptions):
    rag = SemanticRAGService(KNOWLEDGE_FILE)
    mock_resp = LLMEvaluationResponse(
        is_correct=False,
        score=0.25,
        detected_misconceptions=["confuse_assign_equals"],
        diagnosis="Student attempted to solve x = x + 1 as an algebra equation.",
        feedback="In Python, '=' is an assignment operator, not an equation of equality.",
        step_by_step_explanation="1. Compute the right-hand side (x + 1). 2. Store the resulting value back in x.",
        follow_up_challenge="If count = 7, what is count after executing count = count + 3?",
        evaluator_mode="llm_rag_grounded",
        confidence_score=0.95,
    )
    client = MockLLMClient(default_model_instance=mock_resp)
    evaluator = LLMEvaluator(llm_client=client, rag_service=rag)

    req = LLMEvaluationRequest(
        concept_id="py.variables",
        concept_title="Variables and Assignment",
        question="In Python, what is the meaning of x = x + 1?",
        student_response="It has no solution in algebra because x cannot equal x + 1.",
        misconception_catalog=sample_misconceptions,
    )

    res = evaluator.evaluate(req)

    assert res.evaluator_mode == "llm_rag_grounded"
    assert res.is_correct is False
    assert res.score == 0.25
    assert res.detected_misconceptions == ["confuse_assign_equals"]
    assert "assignment operator" in res.feedback
    assert len(client.call_history) == 1

    # Verify RAG ground truth was injected into the prompt
    recorded_prompt = client.call_history[0]["prompt"]
    assert "AUTHORITATIVE REFERENCES:" in recorded_prompt
    assert "Official Python 3 Documentation" in recorded_prompt
    assert "confuse_assign_equals" in recorded_prompt


def test_misconception_sanitization_rejects_hallucinations(sample_misconceptions):
    rag = SemanticRAGService(KNOWLEDGE_FILE)
    # Simulate LLM returning a real ID + an invented hallucination
    mock_resp = LLMEvaluationResponse(
        is_correct=False,
        score=0.3,
        detected_misconceptions=["confuse_assign_equals", "hallucinated_invalid_id_999"],
        diagnosis="Misunderstanding detected.",
        feedback="Notice the difference between equality and assignment.",
        step_by_step_explanation="Step by step trace.",
        evaluator_mode="llm_rag_grounded",
    )
    client = MockLLMClient(default_model_instance=mock_resp)
    evaluator = LLMEvaluator(llm_client=client, rag_service=rag)

    req = LLMEvaluationRequest(
        concept_id="py.variables",
        concept_title="Variables and Assignment",
        question="Explain x = x + 1",
        student_response="impossible algebra equation",
        misconception_catalog=sample_misconceptions,
    )

    res = evaluator.evaluate(req)
    # The valid ID is retained, the hallucinated ID is strictly filtered out
    assert "confuse_assign_equals" in res.detected_misconceptions
    assert "hallucinated_invalid_id_999" not in res.detected_misconceptions


def test_pure_logic_invariant_overrides_llm_hallucinations(sample_misconceptions):
    rag = SemanticRAGService(KNOWLEDGE_FILE)
    # Simulate an LLM mistakenly giving 0% score to correct swap code
    mock_resp = LLMEvaluationResponse(
        is_correct=False,
        score=0.0,
        detected_misconceptions=["simultaneous_assignment_confusion"],
        diagnosis="Model failed to understand compact swap syntax.",
        feedback="Incorrect.",
        step_by_step_explanation="Check your steps.",
        evaluator_mode="llm_rag_grounded",
    )
    client = MockLLMClient(default_model_instance=mock_resp)
    evaluator = LLMEvaluator(llm_client=client, rag_service=rag)

    req = LLMEvaluationRequest(
        concept_id="py.variables",
        concept_title="Variables and Assignment",
        question="Write code to swap x and y.",
        student_response="t=x,x=y,y=t",
        misconception_catalog=sample_misconceptions,
    )

    res = evaluator.evaluate(req)
    # Logic verifier overrides LLM mistake: verified computational state transition!
    assert res.is_correct is True
    assert res.score == 1.0
    assert res.detected_misconceptions == []


def test_fault_tolerant_fallback_on_network_failure(sample_misconceptions):
    rag = SemanticRAGService(KNOWLEDGE_FILE)
    # Simulate API network timeout / connection error
    error_client = MockLLMClient(simulate_error=True)
    evaluator = LLMEvaluator(llm_client=error_client, rag_service=rag)

    req = LLMEvaluationRequest(
        concept_id="py.variables",
        concept_title="Variables and Assignment",
        question="Write code to swap x and y.",
        student_response="temp = x; x = y; y = temp",
        misconception_catalog=sample_misconceptions,
    )

    # Must NOT raise exception; must gracefully fallback to deterministic verifier
    res = evaluator.evaluate(req)
    assert res.evaluator_mode == "rule_fallback"
    assert res.is_correct is True
    assert res.score == 1.0


def test_dynamic_transfer_question_generation():
    rag = SemanticRAGService(KNOWLEDGE_FILE)
    mock_q = GeneratedTransferQuestion(
        concept_id="py.variables",
        prompt="Suppose we run: a = 15; a = a + 5. What is the value stored in a?",
        tip="Evaluate the right-hand side first.",
        expected_answer="20",
        explanation="15 + 5 evaluates to 20, which is then bound to a.",
        target_misconception_id="confuse_assign_equals",
    )
    client = MockLLMClient(default_model_instance=mock_q)
    evaluator = LLMEvaluator(llm_client=client, rag_service=rag)

    misc = Misconception(
        id="confuse_assign_equals",
        name="Algebra Equality Error",
        description="Treats = as equality",
        counter_example="x = x + 1",
        remediation_hint="Explain evaluation order",
    )
    gen_q = evaluator.generate_transfer_question(
        concept_id="py.variables",
        concept_title="Variables and Assignment",
        active_misconception=misc,
    )

    assert gen_q.concept_id == "py.variables"
    assert "a = a + 5" in gen_q.prompt
    assert gen_q.expected_answer == "20"


def test_coordinator_evaluate_student_response_integration():
    with TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_coord_m2.db"
        repo = StudentRepository(db_path)

        student = StudentProfile(
            student_id="stu_m2_test",
            name="Aria",
            target_goal="Learn Python with Socratic AI",
        )

        mock_resp = LLMEvaluationResponse(
            is_correct=True,
            score=0.9,
            detected_misconceptions=[],
            diagnosis="Student understands evaluation order and memory binding.",
            feedback="Excellent explanation of imperative assignment.",
            step_by_step_explanation="The expression on the right is computed first.",
            evaluator_mode="llm_rag_grounded",
        )
        client = MockLLMClient(default_model_instance=mock_resp)

        rag = SemanticRAGService(KNOWLEDGE_FILE, repository=repo)
        evaluator = LLMEvaluator(llm_client=client, rag_service=rag)

        coordinator = TutorCoordinator(
            student_profile=student,
            concepts_file=CONCEPTS_FILE,
            knowledge_file=KNOWLEDGE_FILE,
            mastery_threshold=0.70,
            repository=repo,
            evaluator=evaluator,
            rag_service=rag,
        )

        # Evaluate student response through coordinator
        res = coordinator.evaluate_student_response(
            concept_id="py.variables",
            question="In Python, what is the meaning of x = x + 1?",
            student_response="The right side x + 1 is calculated first, then assigned back to x.",
        )

        assert res["is_correct"] is True
        assert res["score"] == 0.9
        assert res["new_mastery"] > 0.0
        assert res["confidence"] > 0.0
        assert res["evaluator_mode"] == "llm_rag_grounded"

        # Verify state was persisted in SQLite
        loaded_mastery = repo.load_mastery_map("stu_m2_test")
        assert "py.variables" in loaded_mastery
        assert loaded_mastery["py.variables"].mastery == res["new_mastery"]
