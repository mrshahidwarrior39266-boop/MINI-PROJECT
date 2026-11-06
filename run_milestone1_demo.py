"""
Milestone 1 Interactive Simulation & Visual Demo:
Runs a step-by-step demonstration of the Adaptive Learning Assistant engine.
"""
from pathlib import Path
from app.models.student import StudentProfile
from app.services.tutor_coordinator import TutorCoordinator

DATA_DIR = Path(__file__).parent / "app" / "data"
CONCEPTS_FILE = DATA_DIR / "python_concepts.json"
KNOWLEDGE_FILE = DATA_DIR / "python_knowledge.json"


def render_progress_bar(val: float, width: int = 20) -> str:
    filled = int(val * width)
    bar = "=" * filled + "-" * (width - filled)
    return f"[{bar}] {val * 100:5.1f}%"


def print_banner(text: str):
    print("\n" + "=" * 70)
    print(f" {text}")
    print("=" * 70)


def print_state_summary(coordinator: TutorCoordinator):
    frontier = coordinator.get_frontier()
    print("\nCURRENT CURRICULUM STATE:")
    print(f"  * Mastered      ({len(frontier.mastered)}): {', '.join(frontier.mastered) if frontier.mastered else 'None'}")
    print(f"  * In Progress   ({len(frontier.in_progress)}): {', '.join(frontier.in_progress) if frontier.in_progress else 'None'}")
    print(f"  * Ready to Learn({len(frontier.ready)}): {', '.join(frontier.ready) if frontier.ready else 'None'}")
    print(f"  * Locked        ({len(frontier.locked)}): {', '.join(frontier.locked) if frontier.locked else 'None'}")

    print("\nSTUDENT MASTERY BREAKDOWN:")
    for cid, concept in coordinator.graph_service.concepts.items():
        mastery = coordinator.student_service.get_or_create_mastery(cid)
        status = "LOCKED"
        if cid in frontier.mastered:
            status = "MASTERED"
        elif cid in frontier.ready:
            status = "READY"
        elif cid in frontier.in_progress:
            status = "IN PROGRESS"

        miscon_note = f" (Misconceptions: {mastery.active_misconceptions})" if mastery.active_misconceptions else ""
        print(f"  {concept.title:<36} | {render_progress_bar(mastery.mastery)} | {status:<11}{miscon_note}")


def main():
    print_banner("AI-POWERED ADAPTIVE LEARNING ASSISTANT - MILESTONE 1 DEMO")
    
    # Initialize Learner
    student = StudentProfile(
        student_id="stu_007",
        name="Alex",
        target_goal="Learn Python from absolute basics",
        explanation_preference="analogy_heavy"
    )
    
    coordinator = TutorCoordinator(
        student_profile=student,
        concepts_file=CONCEPTS_FILE,
        knowledge_file=KNOWLEDGE_FILE,
        mastery_threshold=0.70
    )

    print(f"Learner initialized: {student.name} ({student.target_goal})")
    print(f"Total curriculum concepts loaded: {len(coordinator.graph_service.concepts)}")
    print_state_summary(coordinator)

    # 1. Recommendation Step
    rec = coordinator.recommend_next_action()
    print_banner(f"STEP 1: Tutor Policy Recommends -> {rec.action_type} '{rec.target_concept_title}'")
    
    # 2. Get lesson materials and citations
    lesson = coordinator.get_lesson_context(rec.target_concept_id)
    print("\nVerified Ground-Truth Context:")
    for chunk in lesson["verified_content_chunks"]:
        print(f"  > \"{chunk[:140]}...\"")
    print("\nOfficial Sources & Citations:")
    print(f"  {lesson['citations']}")

    # 3. Simulate first student interaction: Alex gives an answer with a known misconception
    print_banner("STEP 2: Student Diagnostic Test (Simulated Attempt with Misconception)")
    q1 = "In Python, what is the meaning of x = x + 1?"
    a1 = "It's an algebra equation saying x is equal to x + 1, which has no mathematical solution!"
    print(f"Question: {q1}")
    print(f"Alex's Answer: {a1}")

    eval1 = coordinator.process_student_eval(
        concept_id="py.variables",
        question=q1,
        student_response=a1,
        score=0.3,
        detected_misconceptions=["confuse_assign_equals"],
        feedback="In Python, '=' is variable assignment, not algebraic equality. The right side evaluates first."
    )
    print(f"\nEvaluator Result:")
    print(f"  Score: {eval1['score']} / 1.0")
    print(f"  Detected Misconception: {eval1['active_misconceptions']}")
    print(f"  New Mastery Score: {eval1['new_mastery']}")
    print(f"  Next Recommended Action: {eval1['next_recommended_goal']['action_type']}")

    print_state_summary(coordinator)

    # 4. Remediation and Success Loop
    print_banner("STEP 3: Targeted Remediation and Successive Practice")
    exercises = [
        (
            "Explain what '=' does in: speed = 60",
            "It binds the label 'speed' to integer 60 in memory.",
            1.0,
            [],
            "Exact definition of reference assignment."
        ),
        (
            "What will this print: a = 5; b = a; a = 9; print(b)",
            "5, because b got a reference to 5, not a permanent reactive link to a.",
            1.0,
            [],
            "Great work! Misconception resolved."
        ),
        (
            "Write a snippet to swap x and y using a temporary variable.",
            "temp = x; x = y; y = temp",
            1.0,
            [],
            "Classic 3-step swap. Mastery threshold reached!"
        )
    ]

    for idx, (q, a, score, misc, fb) in enumerate(exercises, 1):
        print(f"\n--- Practice Task {idx} ---")
        print(f"Q: {q}")
        print(f"A: {a}")
        res = coordinator.process_student_eval("py.variables", q, a, score, misc, fb)
        print(f"Outcome: Score {score} | Mastery: {res['new_mastery']} | Confidence: {res['confidence']}")

    print_banner("STEP 4: CURRICULUM STATE AFTER MASTERY VERIFICATION")
    print_state_summary(coordinator)

    next_rec = coordinator.recommend_next_action()
    print_banner(f"NEXT AUTOMATICALLY UNLOCKED TOPIC: '{next_rec.target_concept_title}'")
    print(f"Action: {next_rec.action_type}")
    print(f"Notice that 'py.data_types' has automatically unlocked because its prerequisite ('py.variables') is now proven mastered.")


if __name__ == "__main__":
    main()
