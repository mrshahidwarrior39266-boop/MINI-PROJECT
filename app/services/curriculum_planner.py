"""
Curriculum Planner Service:
Implements DAG traversal and automated daily session planning according to the
strict pedagogical formula:
- 30% Review (spaced repetition of decaying concepts)
- 60% Frontier Learning (introducing and practicing next unlocked concepts)
- 10% Synthesis Challenge (multi-concept capstone problem)
"""
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Any

from app.models.concept import Concept
from app.models.curriculum import (
    LearningFrontier,
    PlannedExercise,
    DailySessionPlan,
    SynthesisChallenge,
)
from app.models.student import ConceptMastery, StudentProfile
from app.services.concept_graph import ConceptGraphService
from app.services.question_service import QuestionService
from app.services.spaced_repetition import SpacedRepetitionEngine

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_SYNTHESIS_FILE = DATA_DIR / "synthesis_challenges.json"


class CurriculumPlanner:
    """Automates DAG traversal and generates personalized 30/60/10 daily session plans."""

    def __init__(
        self,
        graph_service: ConceptGraphService,
        question_service: QuestionService,
        spaced_repetition_engine: Optional[SpacedRepetitionEngine] = None,
        synthesis_file: Optional[Path] = None,
        mastery_threshold: float = 0.70,
    ):
        self.graph = graph_service
        self.questions = question_service
        self.spaced_engine = spaced_repetition_engine or SpacedRepetitionEngine(
            retention_threshold=mastery_threshold
        )
        self.mastery_threshold = mastery_threshold
        self.synthesis_challenges: List[SynthesisChallenge] = []
        self._load_synthesis_challenges(synthesis_file or DEFAULT_SYNTHESIS_FILE)

    def _load_synthesis_challenges(self, file_path: Path) -> None:
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.synthesis_challenges = [SynthesisChallenge(**item) for item in data]

    def generate_daily_plan(
        self,
        student_profile: StudentProfile,
        mastery_map: Dict[str, ConceptMastery],
        target_total_items: int = 10,
        simulated_days_elapsed: Optional[Dict[str, float]] = None,
    ) -> DailySessionPlan:
        """
        Generate a personalized daily study plan strictly partitioned into:
        - 30% Review (Spaced repetition of decayed concepts or active misconceptions)
        - 60% Frontier Learning (Active frontier concepts: prereqs >= 0.7, target < 0.7)
        - 10% Synthesis Challenge (Multi-concept capstone problem)
        """
        frontier = self.graph.calculate_frontier(mastery_map, self.mastery_threshold)

        # 1. Target bucket item counts
        target_rev = max(1, round(target_total_items * 0.30))
        target_syn = max(1, round(target_total_items * 0.10))
        target_fro = target_total_items - target_rev - target_syn

        review_items: List[PlannedExercise] = []
        frontier_items: List[PlannedExercise] = []
        synthesis_items: List[PlannedExercise] = []

        item_idx = 1

        # -------------------------------------------------------------
        # BUCKET 1: 30% REVIEW (Spaced Repetition & Misconceptions)
        # -------------------------------------------------------------
        review_candidates = self.spaced_engine.rank_concepts_for_review(
            mastery_map, simulated_days_map=simulated_days_elapsed
        )

        for cid, urgency in review_candidates:
            if len(review_items) >= target_rev:
                break
            concept = self.graph.concepts.get(cid)
            if not concept:
                continue

            c_questions = self.questions.get_questions_for_concept(cid)
            if not c_questions:
                continue

            q = c_questions[0]
            m = mastery_map[cid]
            eff_mastery = self.spaced_engine.calculate_decayed_mastery(
                m, simulated_days_elapsed=simulated_days_elapsed.get(cid) if simulated_days_elapsed else None
            )

            reason = (
                f"Active cognitive misconception ({', '.join(m.active_misconceptions)}) requires targeted repair."
                if m.active_misconceptions
                else f"Memory decay: Retention dropped to {eff_mastery * 100:.1f}%. Spaced repetition review."
            )

            ex = PlannedExercise(
                item_index=item_idx,
                bucket="REVIEW",
                concept_id=cid,
                concept_title=concept.title,
                exercise_prompt=q.prompt,
                hint=q.hint,
                canonical_answer=q.canonical_answer,
                estimated_minutes=2,
                rationale=reason,
                decay_score=eff_mastery,
            )
            review_items.append(ex)
            item_idx += 1

        # If more review items are needed to reach target_rev and candidates exist:
        while len(review_items) < target_rev and review_candidates:
            cid, urgency = review_candidates[0]
            concept = self.graph.concepts.get(cid)
            c_questions = self.questions.get_questions_for_concept(cid)
            if not c_questions or not concept:
                break
            q = c_questions[-1]
            m = mastery_map[cid]
            eff_mastery = self.spaced_engine.calculate_decayed_mastery(
                m, simulated_days_elapsed=simulated_days_elapsed.get(cid) if simulated_days_elapsed else None
            )
            ex = PlannedExercise(
                item_index=item_idx,
                bucket="REVIEW",
                concept_id=cid,
                concept_title=concept.title,
                exercise_prompt=f"[Deep Reinforcement] {q.prompt}",
                hint=q.hint,
                canonical_answer=q.canonical_answer,
                estimated_minutes=2,
                rationale=f"Targeted spaced repetition drill to lock in '{concept.title}' memory stability.",
                decay_score=eff_mastery,
            )
            review_items.append(ex)
            item_idx += 1

        # If learner is cold-start (no previous concepts learned to review),
        # allocate surplus items to Frontier Learning
        surplus_slots = target_rev - len(review_items)
        allocated_frontier_slots = target_fro + surplus_slots

        # -------------------------------------------------------------
        # BUCKET 2: 60% FRONTIER LEARNING (Next Unlocked in DAG)
        # -------------------------------------------------------------
        frontier_order: List[str] = []
        # First priority: in_progress concepts (partially attempted, prerequisites met)
        frontier_order.extend(frontier.in_progress)
        # Second priority: ready concepts (all prerequisites >= threshold, not yet started)
        for r_cid in frontier.ready:
            if r_cid not in frontier_order:
                frontier_order.append(r_cid)

        # If frontier is empty but not all concepts mastered, take first unlocked
        if not frontier_order:
            for cid in self.graph.topological_sort():
                if cid not in frontier.mastered:
                    frontier_order.append(cid)
                    break

        for cid in frontier_order:
            if len(frontier_items) >= allocated_frontier_slots:
                break
            concept = self.graph.concepts.get(cid)
            if not concept:
                continue

            c_questions = self.questions.get_questions_for_concept(cid)
            for q_idx, q in enumerate(c_questions):
                if len(frontier_items) >= allocated_frontier_slots:
                    break
                is_intro = q_idx == 0 and cid in frontier.ready
                reason = (
                    f"Active Learning Frontier: Prerequisites satisfied (>= {self.mastery_threshold * 100:.0f}%). "
                    f"{'Introducing new core concept.' if is_intro else 'Reinforcing mastery on frontier.'}"
                )
                ex = PlannedExercise(
                    item_index=item_idx,
                    bucket="FRONTIER",
                    concept_id=cid,
                    concept_title=concept.title,
                    exercise_prompt=q.prompt,
                    hint=q.hint,
                    canonical_answer=q.canonical_answer,
                    estimated_minutes=3,
                    rationale=reason,
                )
                frontier_items.append(ex)
                item_idx += 1

        # If more frontier items are needed to reach allocated_frontier_slots:
        while len(frontier_items) < allocated_frontier_slots and frontier_order:
            for cid in frontier_order:
                if len(frontier_items) >= allocated_frontier_slots:
                    break
                concept = self.graph.concepts.get(cid)
                if not concept:
                    continue
                c_questions = self.questions.get_questions_for_concept(cid)
                if not c_questions:
                    continue
                q = c_questions[-1]
                ex = PlannedExercise(
                    item_index=item_idx,
                    bucket="FRONTIER",
                    concept_id=cid,
                    concept_title=concept.title,
                    exercise_prompt=f"[Mastery Practice] {q.prompt}",
                    hint=q.hint,
                    canonical_answer=q.canonical_answer,
                    estimated_minutes=3,
                    rationale=f"Repeated evidence drill on frontier concept '{concept.title}' to reach 70% threshold.",
                )
                frontier_items.append(ex)
                item_idx += 1

        # -------------------------------------------------------------
        # BUCKET 3: 10% SYNTHESIS CHALLENGE (Multi-Concept Capstone)
        # -------------------------------------------------------------
        candidate_challenges: List[SynthesisChallenge] = []
        for ch in self.synthesis_challenges:
            # Check if learner has touched or mastered at least one of the concepts
            knows_any = any(
                mastery_map.get(cid, ConceptMastery(concept_id=cid)).mastery > 0.0
                for cid in ch.required_concept_ids
            )
            if knows_any or not review_candidates:
                candidate_challenges.append(ch)

        chosen_challenge = (
            candidate_challenges[0] if candidate_challenges else self.synthesis_challenges[0]
        )

        syn_ex = PlannedExercise(
            item_index=item_idx,
            bucket="SYNTHESIS",
            concept_id="synthesis",
            concept_title=f"Synthesis: {chosen_challenge.title}",
            exercise_prompt=chosen_challenge.prompt,
            hint=chosen_challenge.hint,
            canonical_answer=chosen_challenge.canonical_answer,
            estimated_minutes=5,
            rationale=f"Multi-concept synthesis problem integrating: {', '.join(chosen_challenge.required_concept_ids)}.",
        )
        synthesis_items.append(syn_ex)
        item_idx += 1

        # All scheduled items in order: Review first, then Frontier, then Synthesis capstone
        all_items: List[PlannedExercise] = review_items + frontier_items + synthesis_items
        for idx, itm in enumerate(all_items, 1):
            itm.item_index = idx

        total_est_minutes = sum(itm.estimated_minutes for itm in all_items)
        now_str = datetime.now(timezone.utc).isoformat()
        session_id = f"plan_{student_profile.student_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        rev_pct = (len(review_items) / len(all_items)) * 100
        fro_pct = (len(frontier_items) / len(all_items)) * 100
        syn_pct = (len(synthesis_items) / len(all_items)) * 100

        ratio_str = f"{rev_pct:.0f}% Review | {fro_pct:.0f}% Frontier Learning | {syn_pct:.0f}% Synthesis Challenge"

        return DailySessionPlan(
            session_id=session_id,
            student_id=student_profile.student_id,
            student_name=student_profile.name,
            generated_at=now_str,
            target_total_items=target_total_items,
            review_items=review_items,
            frontier_items=frontier_items,
            synthesis_items=synthesis_items,
            all_scheduled_items=all_items,
            frontier_summary=frontier,
            estimated_total_minutes=total_est_minutes,
            ratio_summary=ratio_str,
        )

    @staticmethod
    def format_plan_display(plan: DailySessionPlan) -> str:
        """Render a beautifully structured terminal dashboard for the daily study plan."""
        lines = [
            "=" * 70,
            f" PERSONALIZED DAILY STUDY PLAN for {plan.student_name.upper()}".center(70),
            "=" * 70,
            f" Plan ID : {plan.session_id}",
            f" Target  : {len(plan.all_scheduled_items)} Exercises (~{plan.estimated_total_minutes} Minutes Total)",
            f" Ratios  : {plan.ratio_summary}",
            "-" * 70,
            " ACTIVE LEARNING FRONTIER SNAPSHOT:",
            f"  * Mastered Topics : {len(plan.frontier_summary.mastered)}",
            f"  * In Progress     : {len(plan.frontier_summary.in_progress)}",
            f"  * Ready to Unlock : {len(plan.frontier_summary.ready)} ({', '.join(plan.frontier_summary.ready) or 'None'})",
            f"  * Locked Behind Prereqs : {len(plan.frontier_summary.locked)}",
            "-" * 70,
            " SCHEDULED DAILY EXERCISES:",
        ]

        bucket_icons = {
            "REVIEW": "[30% REVIEW]",
            "FRONTIER": "[60% FRONTIER]",
            "SYNTHESIS": "[10% SYNTHESIS]",
        }

        for item in plan.all_scheduled_items:
            tag = bucket_icons.get(item.bucket, item.bucket)
            decay_note = f" (Decayed to {item.decay_score * 100:.0f}%)" if item.decay_score is not None else ""
            lines.extend([
                f"\n [{item.item_index:02d}] {tag:<15} | {item.concept_title}{decay_note}",
                f"      Rationale : {item.rationale}",
                f"      Prompt    : {item.exercise_prompt[:95]}...",
            ])

        lines.extend([
            "\n" + "=" * 70,
            " Ready to learn? Follow this plan in sequence to maximize memory retention!",
            "=" * 70,
        ])
        return "\n".join(lines)
