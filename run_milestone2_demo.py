"""
Milestone 2 Visual Demo:
Demonstration of Dense Semantic RAG, Socratic LLM Evaluation,
Logic Invariant Guarantees, and Resilient Fault-Tolerant Fallbacks.
"""
import sys
from pathlib import Path

from app.models.concept import Misconception
from app.models.student import StudentProfile
from app.models.evaluator import (
    LLMEvaluationRequest,
    LLMEvaluationResponse,
    GeneratedTransferQuestion,
)
from app.services.embedding_service import DeterministicSemanticEmbedding
from app.services.semantic_rag import SemanticRAGService
from app.services.llm_client import MockLLMClient
from app.services.llm_evaluator import LLMEvaluator
from app.services.tutor_coordinator import TutorCoordinator
from app.services.logic_verifier import LogicVerifier

DATA_DIR = Path(__file__).resolve().parent / "app" / "data"
CONCEPTS_FILE = DATA_DIR / "python_concepts.json"
KNOWLEDGE_FILE = DATA_DIR / "python_knowledge.json"


def configure_console() -> None:
    """Use UTF-8 on Windows consoles so section symbols and citations never crash or garble."""
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if stream is None:
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def print_banner(text: str) -> None:
    print("\n" + "=" * 70)
    print(f" {text}")
    print("=" * 70)


def print_section(text: str) -> None:
    print("\n" + "-" * 70)
    print(f" {text}")
    print("-" * 70)


def main():
    configure_console()
    print_banner("AI-POWERED ADAPTIVE LEARNING ASSISTANT - MILESTONE 2 DEMO")
    print("Milestone 2 introduces Dense Semantic RAG & Socratic LLM Evaluation.")
    print("Featuring: Dense vector embeddings, grounded RAG, misconception diagnosis,")
    print("AST logic verification, and 100% resilient offline fallback.")

    # -------------------------------------------------------------------------
    # PART 1: DENSE SEMANTIC RAG RETRIEVAL
    # -------------------------------------------------------------------------
    print_banner("PART 1: DENSE SEMANTIC VECTOR RETRIEVAL (KNOWLEDGE RAG)")
    rag = SemanticRAGService(KNOWLEDGE_FILE)
    print(f"Loaded {len(rag.chunks_by_id)} authoritative textbook chunks across 8 curriculum nodes.")
    print(f"Embedding Provider: {rag.embedding_service.provider_name} (Dimension: {rag.embedding_service.dimension})")

    demo_queries = [
        "In Python, what is the meaning of x = x + 1?",
        "how to iterate through list of items using for loop and range",
        "breaking out of while True loop when condition is met",
    ]

    for q in demo_queries:
        print_section(f"Query: '{q}'")
        res = rag.retrieve(q, top_k=2)
        print(f"Retrieval Time: {res.retrieval_time_ms:.2f} ms")
        for rank, m in enumerate(res.matches, 1):
            c = m.chunk
            print(f"  [{rank}] Concept: {c.concept_id:<22} | Cosine Sim: {m.similarity_score:.4f} | Reliability: {c.reliability_score:.2f}")
            print(f"      Source: {c.source_title}")
            print(f"      Snippet: \"{c.content[:115]}...\"")

    # -------------------------------------------------------------------------
    # PART 2: GROUNDED SOCRATIC LLM EVALUATION WITH MISCONCEPTION DIAGNOSIS
    # -------------------------------------------------------------------------
    print_banner("PART 2: GROUNDED SOCRATIC LLM EVALUATION & MISCONCEPTION DIAGNOSIS")

    sample_misc = [
        Misconception(
            id="confuse_assign_equals",
            name="Confusing Assignment with Algebraic Equality",
            description="Treats = as algebraic equality rather than imperative assignment.",
            counter_example="x = x + 1 is valid in Python.",
            remediation_hint="Explain evaluation order (right side first, then store left).",
        )
    ]

    mock_llm_response = LLMEvaluationResponse(
        is_correct=False,
        score=0.20,
        detected_misconceptions=["confuse_assign_equals"],
        diagnosis="Student attempted to interpret x = x + 1 as an algebraic equality rather than memory binding.",
        feedback="In Python, the '=' symbol is not a mathematical equation of balance; it is an assignment command.",
        step_by_step_explanation="1. Python evaluates the right-hand side expression (x + 1) first.\n2. It then binds that resulting value to the variable name 'x' on the left side.",
        follow_up_challenge="If count = 5, what is the value of count after: count = count + 4?",
        evaluator_mode="llm_rag_grounded",
        confidence_score=0.98,
    )
    llm_client = MockLLMClient(default_model_instance=mock_llm_response)
    evaluator = LLMEvaluator(llm_client=llm_client, rag_service=rag)

    q_text = "In Python, what is the meaning of x = x + 1?"
    student_ans = "It's an algebra equation saying x is equal to x + 1, which has no mathematical solution!"
    print(f"Tutor Question   : {q_text}")
    print(f"Student Response : \"{student_ans}\"")

    req = LLMEvaluationRequest(
        concept_id="py.variables",
        concept_title="Variables and Assignment",
        question=q_text,
        student_response=student_ans,
        misconception_catalog=sample_misc,
        student_preference="analogy_heavy",
    )

    eval_result = evaluator.evaluate(req)

    print("\nEVALUATOR RESULTS:")
    print(f"  * Evaluator Mode        : {eval_result.evaluator_mode}")
    print(f"  * Is Correct            : {eval_result.is_correct}")
    print(f"  * Score                 : {eval_result.score:.2f} / 1.00")
    print(f"  * Detected Misconceptions: {eval_result.detected_misconceptions}")
    print(f"  * Pedagogical Diagnosis : {eval_result.diagnosis}")
    print(f"  * Socratic Feedback     : {eval_result.feedback}")
    print("\nSTEP-BY-STEP EXPLANATION:")
    for line in eval_result.step_by_step_explanation.split("\n"):
        print(f"  {line}")

    # -------------------------------------------------------------------------
    # PART 3: PURE COMPUTATIONAL LOGIC VERIFICATION (AST INVARIANTS)
    # -------------------------------------------------------------------------
    print_banner("PART 3: PURE COMPUTATIONAL LOGIC VERIFIER (AST INVARIANTS)")
    print("Testing student variable swap: 't=x,x=y,y=t' (independent of variable names)")

    swap_req = LLMEvaluationRequest(
        concept_id="py.variables",
        concept_title="Variables and Assignment",
        question="Write code to swap x and y without data loss.",
        student_response="t=x,x=y,y=t",
        misconception_catalog=sample_misc,
    )
    swap_res = evaluator.evaluate(swap_req)
    print(f"  * Code Submitted : 't=x,x=y,y=t'")
    print(f"  * Correctness    : {swap_res.is_correct} (Score: {swap_res.score:.2f})")
    print(f"  * AST Invariant  : {swap_res.diagnosis}")

    # -------------------------------------------------------------------------
    # PART 4: DYNAMIC Socratic TRANSFER QUESTION GENERATION
    # -------------------------------------------------------------------------
    print_banner("PART 4: DYNAMIC Socratic TRANSFER QUESTION GENERATION")
    llm_client.register_model_instance(
        GeneratedTransferQuestion(
            concept_id="py.variables",
            prompt="Suppose we execute: count = 10; count = count + 5. What value is stored in count, and why?",
            tip="Remember the 2-step evaluation order: compute right side first, then rebind the variable on the left.",
            expected_answer="15",
            explanation="10 + 5 is evaluated first giving 15, which is then assigned back to the variable count.",
            target_misconception_id="confuse_assign_equals",
        )
    )
    gen_transfer = evaluator.generate_transfer_question(
        concept_id="py.variables",
        concept_title="Variables and Assignment",
        active_misconception=sample_misc[0],
    )
    print(f"Generated Question : {gen_transfer.prompt}")
    print(f"Tip / Hint         : {gen_transfer.tip}")
    print(f"Expected Answer    : {gen_transfer.expected_answer}")

    # -------------------------------------------------------------------------
    # PART 5: FAULT-TOLERANT OFFLINE FALLBACK GUARANTEE
    # -------------------------------------------------------------------------
    print_banner("PART 5: FAULT-TOLERANT OFFLINE FALLBACK GUARANTEE")
    print("Simulating API outage or network interruption (MockLLMClient: simulate_error=True)...")
    offline_evaluator = LLMEvaluator(
        llm_client=MockLLMClient(simulate_error=True),
        rag_service=rag,
    )
    fallback_res = offline_evaluator.evaluate(swap_req)
    print(f"  * Fallback Active : {fallback_res.evaluator_mode == 'rule_fallback'}")
    print(f"  * Mode Returned   : {fallback_res.evaluator_mode}")
    print(f"  * System Crash    : None (Graceful recovery succeeded!)")

    print_banner("MILESTONE 2 DEMO COMPLETE: ALL SUBSYSTEMS OPERATIONAL")


if __name__ == "__main__":
    main()
