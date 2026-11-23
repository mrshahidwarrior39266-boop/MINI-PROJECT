"""
LLM Socratic Evaluator Service.

Implements:
- Structured Socratic evaluation with grounded Dense RAG context
- Cognitive misconception diagnosis mapped to formal concept catalogs
- Pure computational logic verification integration
- Transparent, resilient fallback to deterministic rules when offline
"""
import logging
from typing import List, Optional, Set

from app.models.concept import KnowledgeChunk, Misconception
from app.models.evaluator import (
    LLMEvaluationRequest,
    LLMEvaluationResponse,
    GeneratedTransferQuestion,
)
from app.services.llm_client import BaseLLMClient
from app.services.semantic_rag import SemanticRAGService
from app.services.question_service import QuestionService
from app.services.logic_verifier import LogicVerifier
from app.services.beginner_pedagogy import BeginnerPedagogyService

logger = logging.getLogger(__name__)


class LLMEvaluator:
    """Socratic LLM Evaluator with Dense Semantic RAG and rule-based fallback."""

    SYSTEM_PROMPT = """You are an expert Socratic Computer Science Tutor and Educational Diagnostician.
Your task is to evaluate a student's answer to a programming question.

PEDAGOGICAL PRINCIPLES:
1. FOCUS ON CONCEPTUAL LOGIC: Prioritize computational understanding over superficial naming or syntax formatting.
2. STRICT EVIDENCE GROUNDING: Grade strictly against the provided Authoritative Ground Truth References. Never hallucinate rules outside real Python mechanics.
3. MISCONCEPTION DIAGNOSIS: If the student makes an error, match it to one or more known Misconception IDs from the catalog. Do NOT invent new IDs.
4. SOCRATIC FEEDBACK: Provide encouraging, growth-minded feedback. Point out the mechanical breakdown without simply giving away the answer. Use physical real-world analogies (cardboard boxes, water cups, conveyor belts) to clarify points.
5. CONSTRUCTIVE EXPLANATION: Clearly explain the underlying memory, evaluation order, or runtime behavior step by step.
6. MANDATORY CITATION ENFORCEMENT: You MUST cite at least one reference chunk ID from the provided reference list in the `cited_chunk_ids` array.
"""

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        rag_service: Optional[SemanticRAGService] = None,
        question_service: Optional[QuestionService] = None,
        logic_verifier: Optional[LogicVerifier] = None,
        pedagogy_service: Optional[BeginnerPedagogyService] = None,
    ):
        self.llm_client = llm_client
        self.rag_service = rag_service
        self.question_service = question_service
        self.logic_verifier = logic_verifier or LogicVerifier()
        self.pedagogy_service = pedagogy_service

    def evaluate(self, request: LLMEvaluationRequest) -> LLMEvaluationResponse:
        """Evaluate student response using LLM with RAG grounding, with automatic fallback."""
        # Check pure computational logic invariant first if response is Python code
        is_verified_swap = self._check_logic_invariants(request)

        # Attempt LLM evaluation if client is available
        if self.llm_client is not None:
            try:
                return self._evaluate_with_llm(request, is_verified_swap)
            except Exception as exc:
                logger.warning(f"LLM evaluation failed ({exc}); seamlessly falling back to deterministic rules.")

        # Fallback to deterministic rules
        return self._evaluate_with_fallback(request, is_verified_swap)

    def _check_logic_invariants(self, request: LLMEvaluationRequest) -> bool:
        """Check if student's answer fulfills pure computational logic (e.g. variable swapping)."""
        prompt_lower = request.question.lower()
        if "swap" in prompt_lower or "variable" in prompt_lower:
            result = self.logic_verifier.verify_swap(request.student_response)
            if result.is_valid:
                return True
        return False

    def _evaluate_with_llm(
        self, request: LLMEvaluationRequest, is_verified_swap: bool
    ) -> LLMEvaluationResponse:
        """Execute structured LLM Socratic evaluation grounded in dense RAG."""
        # Retrieve relevant RAG context
        reference_chunks = list(request.reference_chunks)
        if self.rag_service is not None and not reference_chunks:
            retrieval = self.rag_service.retrieve(
                query=f"{request.question}\n{request.student_response}",
                concept_id=request.concept_id,
                top_k=3,
            )
            reference_chunks = [m.chunk for m in retrieval.matches]

        # Format prompt sections
        ground_truth_text = self._format_ground_truth(reference_chunks)
        misconceptions_text = self._format_misconceptions(request.misconception_catalog)
        pedagogy_text = ""
        if self.pedagogy_service:
            pedagogy_text = "\n" + self.pedagogy_service.enrich_prompt_for_llm(request.concept_id)

        prompt = f"""EVALUATION TASK:
Target Concept: {request.concept_title} (ID: {request.concept_id})
Student Learning Style: {request.student_preference}
{pedagogy_text}
{ground_truth_text}

{misconceptions_text}

TUTOR QUESTION:
{request.question}

STUDENT'S SUBMITTED ANSWER:
"{request.student_response}"

Evaluate the student's answer and return structured JSON."""

        response: LLMEvaluationResponse = self.llm_client.complete_structured(
            prompt=prompt,
            response_model=LLMEvaluationResponse,
            system_prompt=self.SYSTEM_PROMPT,
        )

        # Sanitize and validate detected misconception IDs against concept catalog
        valid_ids: Set[str] = {m.id for m in request.misconception_catalog}
        sanitized_misconceptions = [m for m in response.detected_misconceptions if m in valid_ids]

        # Enforce logic verifier override if AST proved correct state transitions
        score = response.score
        is_correct = response.is_correct
        if is_verified_swap:
            score = max(score, 1.0)
            is_correct = True
            sanitized_misconceptions = []

        # Enforce source citations referencing knowledge chunk IDs
        available_ids = [c.id for c in reference_chunks]
        cited_ids = [cid for cid in response.cited_chunk_ids if cid in available_ids]
        if not cited_ids and available_ids:
            # Enforce provenance: inject the top-ranked retrieved chunk ID
            cited_ids = [available_ids[0]]

        return LLMEvaluationResponse(
            is_correct=is_correct,
            score=max(0.0, min(1.0, score)),
            detected_misconceptions=sanitized_misconceptions,
            diagnosis=response.diagnosis,
            feedback=response.feedback,
            step_by_step_explanation=response.step_by_step_explanation,
            cited_chunk_ids=cited_ids,
            follow_up_challenge=response.follow_up_challenge,
            evaluator_mode="llm_rag_grounded",
            confidence_score=response.confidence_score,
        )

    def _evaluate_with_fallback(
        self, request: LLMEvaluationRequest, is_verified_swap: bool
    ) -> LLMEvaluationResponse:
        """Deterministic rule & AST fallback evaluation."""
        fallback_citations = [c.id for c in request.reference_chunks] if request.reference_chunks else []
        if not fallback_citations and self.rag_service is not None:
            retrieval = self.rag_service.retrieve(
                query=f"{request.question}\n{request.student_response}",
                concept_id=request.concept_id,
                top_k=2,
            )
            fallback_citations = [m.chunk.id for m in retrieval.matches]

        if is_verified_swap:
            return LLMEvaluationResponse(
                is_correct=True,
                score=1.0,
                detected_misconceptions=[],
                diagnosis="Code successfully and cleanly swapped the variables in memory without data loss.",
                feedback="Correct! Your logic successfully executed the 3-step value transfer in memory.",
                step_by_step_explanation="The intermediate variable safely preserved the original value before reassignment, satisfying all state invariants.",
                canonical_answer="temp = x\nx = y\ny = temp\n# or in Python: x, y = y, x",
                cited_chunk_ids=fallback_citations,
                evaluator_mode="rule_fallback",
                confidence_score=1.0,
            )

        if self.question_service is not None:
            # Match against question service catalog
            eval_res = self.question_service.evaluate(request.concept_id, request.student_response, request.question)
            return LLMEvaluationResponse(
                is_correct=eval_res.is_correct,
                score=eval_res.score,
                detected_misconceptions=eval_res.detected_misconceptions,
                diagnosis=eval_res.diagnosis or ("Correct conceptual understanding." if eval_res.is_correct else "Incorrect understanding of mechanism."),
                feedback=eval_res.feedback,
                step_by_step_explanation=eval_res.step_by_step_explanation or eval_res.explanation or "Review the step-by-step mechanism.",
                canonical_answer=getattr(eval_res, "canonical_answer", ""),
                cited_chunk_ids=fallback_citations,
                follow_up_challenge=eval_res.followup_question.prompt if eval_res.followup_question else None,
                evaluator_mode="rule_fallback",
                confidence_score=1.0,
            )

        # Baseline fallback if no rule service is attached
        return LLMEvaluationResponse(
            is_correct=False,
            score=0.0,
            detected_misconceptions=[],
            diagnosis="Response could not be evaluated by LLM or rule engine.",
            feedback="Your response was recorded. Let's review the reference material together.",
            step_by_step_explanation="Review the core concepts before proceeding.",
            cited_chunk_ids=fallback_citations,
            evaluator_mode="rule_fallback",
            confidence_score=0.5,
        )

    def generate_transfer_question(
        self,
        concept_id: str,
        concept_title: str,
        active_misconception: Optional[Misconception] = None,
    ) -> GeneratedTransferQuestion:
        """Dynamically generate a targeted transfer challenge using LLM + RAG."""
        if self.llm_client is not None:
            try:
                # Retrieve RAG chunks
                chunks = []
                if self.rag_service is not None:
                    chunks = self.rag_service.get_concept_ground_truth(concept_id)

                ground_truth = self._format_ground_truth(chunks)
                misc_focus = ""
                if active_misconception:
                    misc_focus = (
                        f"TARGET MISCONCEPTION TO TEST:\n"
                        f"- Name: {active_misconception.name}\n"
                        f"- Description: {active_misconception.description}\n"
                        f"- Counter-example: {active_misconception.counter_example}\n"
                    )

                prompt = f"""Generate a fresh transfer learning question for:
Concept: {concept_title} ({concept_id})

{ground_truth}

{misc_focus}

Create a single concise question that tests practical application and confirms the student has overcome this misconception."""

                res: GeneratedTransferQuestion = self.llm_client.complete_structured(
                    prompt=prompt,
                    response_model=GeneratedTransferQuestion,
                    system_prompt="You are a curriculum designer writing transfer challenge problems in Python.",
                )
                return res
            except Exception as exc:
                logger.warning(f"Dynamic question generation failed ({exc}); using curriculum bank.")

        # Default fallback transfer question
        return GeneratedTransferQuestion(
            concept_id=concept_id,
            prompt=f"Now apply this mechanism to a fresh scenario: Explain how the values change step by step.",
            tip="Trace through the code line by line.",
            expected_answer="Correct line by line execution trace.",
            explanation="Each statement executes sequentially in memory.",
            target_misconception_id=active_misconception.id if active_misconception else None,
        )

    def _format_ground_truth(self, chunks: List[KnowledgeChunk]) -> str:
        if not chunks:
            return "AUTHORITATIVE REFERENCES:\nNo specific reference chunks available."
        lines = ["AUTHORITATIVE REFERENCES: (You MUST cite relevant chunk IDs in 'cited_chunk_ids')"]
        for idx, c in enumerate(chunks, 1):
            lines.append(f"[{idx}] Chunk ID: '{c.id}' | Source: {c.source_title} (Reliability: {c.reliability_score:.2f})")
            lines.append(f"Content: {c.content}")
        return "\n".join(lines)

    def _format_misconceptions(self, misconceptions: List[Misconception]) -> str:
        if not misconceptions:
            return "MISCONCEPTION CATALOG:\nNo known misconceptions cataloged."
        lines = ["MISCONCEPTION CATALOG (Match ONLY to these valid IDs):"]
        for m in misconceptions:
            lines.append(f"- ID: {m.id}")
            lines.append(f"  Name: {m.name}")
            lines.append(f"  Description: {m.description}")
            lines.append(f"  Counter-example: {m.counter_example}")
            lines.append(f"  Remediation Hint: {m.remediation_hint}")
        return "\n".join(lines)
