"""
Tutor Coordinator:
The central orchestration layer for Milestone 1.
Coordinates the Subject Concept Graph, the Knowledge Base, and the Student State.
"""
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from app.models.student import StudentProfile, ConceptMastery
from app.models.curriculum import LearningFrontier, SessionGoal, DailySessionPlan
from app.models.evaluator import LLMEvaluationRequest, LLMEvaluationResponse
from app.models.rag import RetrievalResult, IngestionSummary
from app.services.concept_graph import ConceptGraphService
from app.services.knowledge_base import KnowledgeBaseService
from app.services.student_state import StudentStateService
from app.services.semantic_rag import SemanticRAGService
from app.services.llm_evaluator import LLMEvaluator
from app.services.beginner_pedagogy import BeginnerPedagogyService


class TutorCoordinator:
    def __init__(
        self,
        student_profile: StudentProfile,
        concepts_file: Path,
        knowledge_file: Path,
        mastery_threshold: float = 0.70,
        repository: Optional[Any] = None,
        evaluator: Optional[LLMEvaluator] = None,
        rag_service: Optional[SemanticRAGService] = None,
        pedagogy_service: Optional[BeginnerPedagogyService] = None,
    ):
        if not 0.0 < mastery_threshold <= 1.0:
            raise ValueError("mastery_threshold must be greater than 0 and at most 1.")

        self.repository = repository
        self.graph_service = ConceptGraphService(concepts_file)
        self.knowledge_service = KnowledgeBaseService(knowledge_file)
        self.student_service = StudentStateService(student_profile, repository=repository)
        self.mastery_threshold = mastery_threshold
        self.pedagogy_service = pedagogy_service or BeginnerPedagogyService()

        if not self.graph_service.concepts:
            raise ValueError(
                "No concepts were loaded. Check app/data/python_concepts.json."
            )
        self.knowledge_service.validate(set(self.graph_service.concepts))

        # Milestone 2: Dense Semantic RAG & LLM Evaluator
        from app.services.question_service import QuestionService
        questions_file = Path(__file__).resolve().parent.parent / "data" / "curriculum_questions.json"
        self.question_service = QuestionService(questions_file)

        self.rag_service = rag_service or SemanticRAGService(
            knowledge_file=knowledge_file,
            repository=repository,
        )
        self.evaluator = evaluator or LLMEvaluator(
            rag_service=self.rag_service,
            pedagogy_service=self.pedagogy_service,
            question_service=self.question_service,
        )
        if self.evaluator and self.evaluator.question_service is None:
            self.evaluator.question_service = self.question_service

    def get_frontier(self) -> LearningFrontier:
        """Compute the active learning frontier for the student."""
        return self.graph_service.compute_learning_frontier(
            mastery_map=self.student_service.mastery_map,
            mastery_threshold=self.mastery_threshold
        )

    def recommend_next_action(self) -> SessionGoal:
        """
        Pedagogical policy for selecting the next action:
        1. Priority 1: Remediate active misconceptions in 'in_progress' concepts.
        2. Priority 2: Advance on 'in_progress' concepts to reach mastery.
        3. Priority 3: Introduce the next 'ready' frontier concept.
        4. Priority 4: If everything unlocked is mastered, curriculum complete.
        """
        if not self.graph_service.concepts:
            raise ValueError("No concepts were loaded.")

        frontier = self.get_frontier()

        # Check in_progress concepts for unresolved misconceptions
        for cid in frontier.in_progress:
            mastery = self.student_service.get_or_create_mastery(cid)
            if mastery.active_misconceptions:
                concept = self.graph_service.concepts[cid]
                return SessionGoal(
                    target_concept_id=cid,
                    target_concept_title=concept.title,
                    action_type="REMEDIATE",
                    active_misconceptions=mastery.active_misconceptions,
                    prerequisites_verified=True
                )
            else:
                concept = self.graph_service.concepts[cid]
                return SessionGoal(
                    target_concept_id=cid,
                    target_concept_title=concept.title,
                    action_type="PRACTICE",
                    active_misconceptions=[],
                    prerequisites_verified=True
                )

        # Check for newly unlocked ready concepts
        if frontier.ready:
            target_id = frontier.ready[0]
            concept = self.graph_service.concepts[target_id]
            return SessionGoal(
                target_concept_id=target_id,
                target_concept_title=concept.title,
                action_type="INTRODUCE",
                active_misconceptions=[],
                prerequisites_verified=True
            )

        if frontier.mastered:
            return SessionGoal(
                target_concept_id=frontier.mastered[-1],
                target_concept_title="All Current Concepts Mastered!",
                action_type="COMPLETE",
                active_misconceptions=[],
                prerequisites_verified=True
            )

        # Fallback (e.g. root concept)
        first_concept = next(iter(self.graph_service.concepts.values()))
        return SessionGoal(
            target_concept_id=first_concept.id,
            target_concept_title=first_concept.title,
            action_type="INTRODUCE",
            active_misconceptions=[],
            prerequisites_verified=True
        )

    def get_lesson_context(self, concept_id: str) -> Dict[str, Any]:
        """Gathers verified domain knowledge, prerequisites, and misconceptions for tutoring."""
        concept = self.graph_service.concepts.get(concept_id)
        if not concept:
            raise KeyError(f"Concept '{concept_id}' does not exist.")

        chunks = self.knowledge_service.get_chunks_for_concept(concept_id)
        citations_str = self.knowledge_service.format_citations(chunks)
        mastery = self.student_service.get_or_create_mastery(concept_id)

        return {
            "concept_id": concept.id,
            "title": concept.title,
            "description": concept.description,
            "learning_objectives": concept.learning_objectives,
            "common_misconceptions": [m.model_dump() for m in concept.misconceptions],
            "current_mastery": mastery.mastery,
            "confidence": mastery.confidence,
            "active_misconceptions": mastery.active_misconceptions,
            "verified_content_chunks": [c.content for c in chunks],
            "citations": citations_str,
            "beginner_mental_model": self.pedagogy_service.get_analogy(concept_id),
        }

    def get_beginner_briefing(self, concept_id: str) -> str:
        """Render a real-world physical analogy and mental movie for absolute beginners."""
        return self.pedagogy_service.format_beginner_briefing(concept_id)

    def process_student_eval(
        self,
        concept_id: str,
        question: str,
        student_response: str,
        score: float,
        detected_misconceptions: Optional[List[str]] = None,
        feedback: str = ""
    ) -> Dict[str, Any]:
        """Record assessment evaluation, update mastery, and compute updated frontier."""
        record, log = self.student_service.record_assessment(
            concept_id=concept_id,
            question=question,
            student_response=student_response,
            score=score,
            detected_misconceptions=detected_misconceptions,
            feedback=feedback
        )
        updated_frontier = self.get_frontier()
        next_goal = self.recommend_next_action()

        return {
            "assessment_id": log.id,
            "score": score,
            "new_mastery": record.mastery,
            "confidence": record.confidence,
            "active_misconceptions": record.active_misconceptions,
            "next_review_due": record.next_review_due.isoformat() if record.next_review_due else None,
            "frontier_ready": updated_frontier.ready,
            "frontier_in_progress": updated_frontier.in_progress,
            "frontier_locked": updated_frontier.locked,
            "frontier_mastered": updated_frontier.mastered,
            "next_recommended_goal": next_goal.model_dump()
        }

    def evaluate_student_response(
        self,
        concept_id: str,
        question: str,
        student_response: str,
    ) -> Dict[str, Any]:
        """Milestone 2 Socratic Evaluation: Combines dense RAG, LLM reasoning, and math mastery."""
        concept = self.graph_service.concepts.get(concept_id)
        if not concept:
            raise KeyError(f"Concept '{concept_id}' does not exist.")

        req = LLMEvaluationRequest(
            concept_id=concept_id,
            concept_title=concept.title,
            question=question,
            student_response=student_response,
            misconception_catalog=concept.misconceptions,
            student_preference=self.student_service.profile.explanation_preference,
        )

        eval_response: LLMEvaluationResponse = self.evaluator.evaluate(req)

        # Update mathematical mastery state using the evidence-based formula
        process_res = self.process_student_eval(
            concept_id=concept_id,
            question=question,
            student_response=student_response,
            score=eval_response.score,
            detected_misconceptions=eval_response.detected_misconceptions,
            feedback=eval_response.feedback,
        )

        return {
            "evaluation": eval_response,
            "is_correct": eval_response.is_correct,
            "score": eval_response.score,
            "diagnosis": eval_response.diagnosis,
            "feedback": eval_response.feedback,
            "step_by_step_explanation": eval_response.step_by_step_explanation,
            "cited_chunk_ids": eval_response.cited_chunk_ids,
            "follow_up_challenge": eval_response.follow_up_challenge,
            "evaluator_mode": eval_response.evaluator_mode,
            "detected_misconceptions": eval_response.detected_misconceptions,
            **process_res,
        }

    def get_semantic_context(
        self, query: str, concept_id: Optional[str] = None, top_k: int = 3
    ) -> RetrievalResult:
        """Query the dense semantic knowledge base."""
        return self.rag_service.retrieve(query=query, concept_id=concept_id, top_k=top_k)

    def ingest_knowledge_document(self, file_path: Union[str, Path]) -> IngestionSummary:
        """Ingest a dynamic Markdown or PDF document, auto-link to DAG concepts, and index."""
        from app.services.concept_linker import ConceptLinkerService

        linker = ConceptLinkerService(
            concepts_catalog=self.graph_service.concepts,
            llm_client=self.evaluator.llm_client if self.evaluator else None,
        )
        return self.rag_service.ingest_document(file_path=file_path, linker=linker)

    def generate_daily_session_plan(
        self,
        target_total_items: int = 10,
        simulated_days_elapsed: Optional[Dict[str, float]] = None,
        question_service: Optional[Any] = None,
    ) -> DailySessionPlan:
        """Generate a personalized daily study plan strictly partitioned into 30% Review, 60% Frontier, 10% Synthesis."""
        from app.services.curriculum_planner import CurriculumPlanner
        from app.services.question_service import QuestionService

        q_service = question_service or (
            self.evaluator.question_service
            if self.evaluator and self.evaluator.question_service
            else QuestionService(Path(__file__).resolve().parent.parent / "data" / "curriculum_questions.json")
        )
        planner = CurriculumPlanner(
            graph_service=self.graph_service,
            question_service=q_service,
            mastery_threshold=self.mastery_threshold,
        )
        return planner.generate_daily_plan(
            student_profile=self.student_service.profile,
            mastery_map=self.student_service.mastery_map,
            target_total_items=target_total_items,
            simulated_days_elapsed=simulated_days_elapsed,
        )


