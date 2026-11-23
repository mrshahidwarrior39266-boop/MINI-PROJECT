"""
Unit and integration tests for Milestone 4:
- DAG Traversal & Topological Sort
- Spaced Repetition & Exponential Ebbinghaus Forgetting Curves
- 30% Review / 60% Frontier / 10% Synthesis Daily Session Planner
- Multi-Concept Synthesis Challenges
"""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

from app.models.student import StudentProfile, ConceptMastery
from app.models.curriculum import DailySessionPlan, PlannedExercise
from app.services.concept_graph import ConceptGraphService
from app.services.question_service import QuestionService
from app.services.spaced_repetition import SpacedRepetitionEngine
from app.services.curriculum_planner import CurriculumPlanner
from app.services.tutor_coordinator import TutorCoordinator

ROOT = Path(__file__).resolve().parent.parent
CONCEPTS_FILE = ROOT / "app" / "data" / "python_concepts.json"
KNOWLEDGE_FILE = ROOT / "app" / "data" / "python_knowledge.json"
QUESTIONS_FILE = ROOT / "app" / "data" / "curriculum_questions.json"


@pytest.fixture
def graph():
    return ConceptGraphService(CONCEPTS_FILE)


@pytest.fixture
def questions():
    return QuestionService(QUESTIONS_FILE)


@pytest.fixture
def sr_engine():
    return SpacedRepetitionEngine(base_stability_days=2.0, retention_threshold=0.70)


def test_topological_sort_curriculum_order(graph):
    """Test that topological sorting produces a valid prerequisite-first sequence."""
    order = graph.topological_sort()
    assert len(order) == len(graph.concepts)

    # Every prerequisite must appear before its dependent
    for idx, cid in enumerate(order):
        prereqs = graph.prerequisites_of.get(cid, set())
        for p in prereqs:
            assert order.index(p) < idx, f"Prerequisite '{p}' must precede '{cid}'"


def test_ebbinghaus_memory_decay_calculation(sr_engine):
    """Test exponential decay calculation over time."""
    mastery = ConceptMastery(
        concept_id="py.variables",
        mastery=0.90,
        confidence=0.95,
        attempts_count=2,
        success_count=2,
    )
    # Day 0: no decay
    ret_day0 = sr_engine.calculate_decayed_mastery(mastery, simulated_days_elapsed=0.0)
    assert ret_day0 == 0.90

    # Day 3: partial decay
    ret_day3 = sr_engine.calculate_decayed_mastery(mastery, simulated_days_elapsed=3.0)
    assert 0.0 < ret_day3 < 0.90

    # Day 10: severe decay below threshold
    ret_day10 = sr_engine.calculate_decayed_mastery(mastery, simulated_days_elapsed=10.0)
    assert ret_day10 < 0.70
    assert sr_engine.is_due_for_review(mastery, simulated_days_elapsed=10.0) is True


def test_stability_growth_with_successes(sr_engine):
    """Test that memory stability S increases with successful recalls."""
    m_low = ConceptMastery(concept_id="c", mastery=0.8, attempts_count=1, success_count=0)
    m_high = ConceptMastery(concept_id="c", mastery=0.8, attempts_count=5, success_count=5)

    s_low = sr_engine.calculate_stability(m_low)
    s_high = sr_engine.calculate_stability(m_high)
    assert s_high > s_low


def test_daily_session_plan_exact_ratios(graph, questions, sr_engine):
    """Test that CurriculumPlanner satisfies the 30% Review / 60% Frontier / 10% Synthesis formula."""
    planner = CurriculumPlanner(
        graph_service=graph,
        question_service=questions,
        spaced_repetition_engine=sr_engine,
        mastery_threshold=0.70,
    )
    student = StudentProfile(student_id="test_01", name="Grace Hopper")

    # Mastered variables & data types with decay, operators in progress
    mastery_map = {
        "py.variables": ConceptMastery(
            concept_id="py.variables",
            mastery=0.95,
            attempts_count=4,
            success_count=4,
        ),
        "py.data_types": ConceptMastery(
            concept_id="py.data_types",
            mastery=0.85,
            attempts_count=3,
            success_count=3,
        ),
    }
    # Simulate elapsed days
    sim_days = {"py.variables": 6.0, "py.data_types": 5.0}

    plan = planner.generate_daily_plan(
        student_profile=student,
        mastery_map=mastery_map,
        target_total_items=10,
        simulated_days_elapsed=sim_days,
    )

    assert len(plan.all_scheduled_items) == 10
    assert len(plan.review_items) == 3       # 30%
    assert len(plan.frontier_items) == 6     # 60%
    assert len(plan.synthesis_items) == 1    # 10%

    # Verify bucket types
    assert all(itm.bucket == "REVIEW" for itm in plan.review_items)
    assert all(itm.bucket == "FRONTIER" for itm in plan.frontier_items)
    assert all(itm.bucket == "SYNTHESIS" for itm in plan.synthesis_items)


def test_cold_start_backfills_review_to_frontier(graph, questions, sr_engine):
    """On Day 1 (no concepts learned yet), review slots are backfilled into frontier learning."""
    planner = CurriculumPlanner(
        graph_service=graph,
        question_service=questions,
        spaced_repetition_engine=sr_engine,
    )
    student = StudentProfile(student_id="cold_start_01", name="Novice")

    # Empty mastery map
    plan = planner.generate_daily_plan(
        student_profile=student,
        mastery_map={},
        target_total_items=10,
    )

    assert len(plan.all_scheduled_items) == 10
    assert len(plan.review_items) == 0
    assert len(plan.frontier_items) == 9  # Backfilled 3 review + 6 frontier
    assert len(plan.synthesis_items) == 1


def test_coordinator_generates_daily_plan():
    """Test TutorCoordinator integration for daily session planning."""
    student = StudentProfile(student_id="coord_test", name="Ada Lovelace")
    coordinator = TutorCoordinator(
        student_profile=student,
        concepts_file=CONCEPTS_FILE,
        knowledge_file=KNOWLEDGE_FILE,
        mastery_threshold=0.70,
    )

    plan = coordinator.generate_daily_session_plan(target_total_items=5)
    assert isinstance(plan, DailySessionPlan)
    assert plan.student_id == "coord_test"
    assert len(plan.all_scheduled_items) == 5
    assert len(plan.synthesis_items) == 1
