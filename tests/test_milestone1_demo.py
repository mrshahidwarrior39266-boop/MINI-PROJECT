from pathlib import Path
from app.models.student import StudentProfile
from app.services.tutor_coordinator import TutorCoordinator

DATA_DIR = Path(__file__).parent.parent / "app" / "data"
CONCEPTS_FILE = DATA_DIR / "python_concepts.json"
KNOWLEDGE_FILE = DATA_DIR / "python_knowledge.json"


def test_end_to_end_adaptive_frontier_flow():
    # 1. Initialize Student and Coordinator
    alice = StudentProfile(student_id="student_alice", name="Alice")
    coordinator = TutorCoordinator(
        student_profile=alice,
        concepts_file=CONCEPTS_FILE,
        knowledge_file=KNOWLEDGE_FILE,
        mastery_threshold=0.70
    )

    # 2. Check initial frontier: Only 'py.variables' should be ready (all others have unfulfilled prereqs)
    initial_frontier = coordinator.get_frontier()
    assert "py.variables" in initial_frontier.ready
    assert "py.data_types" in initial_frontier.locked
    assert "py.functions" in initial_frontier.locked
    assert len(initial_frontier.mastered) == 0

    # 3. Coordinator recommends introducing 'py.variables'
    rec1 = coordinator.recommend_next_action()
    assert rec1.target_concept_id == "py.variables"
    assert rec1.action_type == "INTRODUCE"

    # 4. Fetch lesson materials and verified citations
    lesson_ctx = coordinator.get_lesson_context("py.variables")
    assert "Official Python 3 Documentation" in lesson_ctx["citations"]
    misconception_ids = {m["id"] for m in lesson_ctx["common_misconceptions"]}
    assert {"confuse_assign_equals", "variable_permanent_link"} <= misconception_ids

    # 5. Alice attempts problem, but exhibits 'confuse_assign_equals'
    eval1 = coordinator.process_student_eval(
        concept_id="py.variables",
        question="Is x = x + 1 an algebraic equation?",
        student_response="No, because x cannot equal x + 1, it is mathematically impossible!",
        score=0.3,
        detected_misconceptions=["confuse_assign_equals"],
        feedback="In Python '=' is assignment, not algebraic equality."
    )
    assert "confuse_assign_equals" in eval1["active_misconceptions"]
    assert "py.variables" in eval1["frontier_in_progress"]
    # Next recommendation must be REMEDIATE
    assert eval1["next_recommended_goal"]["action_type"] == "REMEDIATE"

    # 6. Alice receives remediation and succeeds on two consecutive tests
    eval2 = coordinator.process_student_eval(
        concept_id="py.variables",
        question="Explain what '=' does in a = 10",
        student_response="It creates the value 10 and binds the label 'a' to it in memory.",
        score=1.0,
        detected_misconceptions=[],
        feedback="Excellent definition of name binding!"
    )
    # Active misconception is cleared
    assert len(eval2["active_misconceptions"]) == 0

    eval3 = coordinator.process_student_eval(
        concept_id="py.variables",
        question="What is the value of y after: x = 5; y = x; x = 9?",
        student_response="y is 5, because assignment copies the reference, it is not permanently linked.",
        score=1.0,
        detected_misconceptions=[],
        feedback="Perfect understanding of value copying."
    )
    # After 2 successes, mastery is 0.5775 (in_progress, strengthening retention)
    assert eval3["new_mastery"] > 0.50
    assert "py.variables" in eval3["frontier_in_progress"]

    # Problem 4: Final synthesis challenge to verify solid mastery
    eval4 = coordinator.process_student_eval(
        concept_id="py.variables",
        question="Write code to swap two variables a and b without losing values.",
        student_response="temp = a; a = b; b = temp",
        score=1.0,
        detected_misconceptions=[],
        feedback="Spotless variable swap implementation."
    )

    # 7. Check that py.variables crossed mastery threshold (>= 0.70)!
    assert eval4["new_mastery"] >= 0.70
    assert "py.variables" in eval4["frontier_mastered"]

    # 8. Adaptive Magic: py.data_types automatically UNLOCKED from locked into ready!
    assert "py.data_types" in eval4["frontier_ready"]
    assert "py.data_types" not in eval4["frontier_locked"]

    # And the coordinator now recommends introducing py.data_types!
    assert eval4["next_recommended_goal"]["target_concept_id"] == "py.data_types"
    assert eval4["next_recommended_goal"]["action_type"] == "INTRODUCE"
