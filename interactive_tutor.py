"""
Interactive Tutor CLI:
Fully generalized Socratic Tutoring System powered by Universal Curriculum Questions
and Multi-Tier Guided Scaffolding.

Guarantee:
No matter how many times a student answers incorrectly, the tutor NEVER leaves them stuck.
It explains the mechanism, offers transfer challenges, and drops into Guided Scaffolding Mode
to walk them through atomic micro-steps until the guided walkthrough is complete.
"""
import os
import sys
from pathlib import Path
from typing import Optional

from app.models.student import StudentProfile
from app.services.tutor_coordinator import TutorCoordinator
from app.services.question_service import QuestionService
from app.services.student_repository import StudentRepository

DATA_DIR = Path(__file__).parent / "app" / "data"
CONCEPTS_FILE = DATA_DIR / "python_concepts.json"
KNOWLEDGE_FILE = DATA_DIR / "python_knowledge.json"
QUESTIONS_FILE = DATA_DIR / "curriculum_questions.json"
DEFAULT_RECORDS_DB = DATA_DIR / "tutor_records.db"

QUIT_COMMANDS = {"quit", "exit"}
RESTART_COMMANDS = {"restart", "reset", "start over", "interactive_tutor.py", "python interactive_tutor.py"}


def get_records_db_path() -> Optional[Path]:
    """Resolve records database path from environment or default.

    Returns None if ephemeral mode is active (e.g. during testing or explicit opt-out).
    """
    if os.environ.get("TUTOR_EPHEMERAL") == "1":
        return None
    env_path = os.environ.get("TUTOR_DB_PATH")
    if env_path:
        if env_path.strip().lower() in ("none", "off", "ephemeral", "0", ":memory:"):
            return None
        return Path(env_path)
    return DEFAULT_RECORDS_DB


class SessionExit(Exception):
    """Raised when the learner ends the session with quit/exit, Ctrl+C, or end-of-input."""


def configure_console() -> None:
    """Use UTF-8 on Windows consoles so names and citations never crash I/O."""
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if stream is None:
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def read_answer(prompt: str) -> str:
    """Read a non-blank answer; blanks re-prompt instead of accidentally ending the session."""
    while True:
        try:
            raw = input(prompt)
        except (KeyboardInterrupt, EOFError):
            raise SessionExit
        if raw.strip():
            return raw.strip()
        print("  (Please type an answer. Type 'quit' to exit.)")


def wait_for_enter() -> None:
    try:
        raw = input("\n[Press Enter to continue to the next step...]")
    except (KeyboardInterrupt, EOFError):
        raise SessionExit
    # A student who types quit here should leave, not accidentally continue.
    if is_quit(raw):
        raise SessionExit


def is_quit(text: str) -> bool:
    return text.strip().lower() in QUIT_COMMANDS


def is_restart(text: str) -> bool:
    return text.strip().lower() in RESTART_COMMANDS


def render_progress_bar(val: float, width: int = 20) -> str:
    filled = int(val * width)
    bar = "=" * filled + "-" * (width - filled)
    return f"[{bar}] {val * 100:5.1f}%"


def print_header(title: str):
    print("\n" + "=" * 70)
    print(f" {title.center(68)}")
    print("=" * 70)


def print_curriculum_dashboard(coordinator: TutorCoordinator):
    frontier = coordinator.get_frontier()
    print("\n" + "-" * 70)
    print(" YOUR KNOWLEDGE PROGRESS DASHBOARD")
    print("-" * 70)
    for cid, concept in coordinator.graph_service.concepts.items():
        mastery = coordinator.student_service.get_or_create_mastery(cid)
        status = "LOCKED"
        if cid in frontier.mastered:
            status = "MASTERED"
        elif cid in frontier.ready:
            status = "READY"
        elif cid in frontier.in_progress:
            status = "IN PROGRESS"

        count = len(mastery.active_misconceptions)
        misc = (
            f" [! {count} misconception{'s' if count != 1 else ''}]"
            if count else ""
        )
        print(f"  {concept.title:<36} | {render_progress_bar(mastery.mastery)} | {status:<11}{misc}")
    print("-" * 70)


def print_misconception_briefing(coordinator: TutorCoordinator, concept_id: str, active: list):
    """Show the specific thinking bug being repaired, not just a generic 'remediation' header."""
    shown = False
    for mid in active:
        misconception = coordinator.graph_service.get_misconception(concept_id, mid)
        if not misconception:
            continue
        shown = True
        print(f"\n Misconception to fix: {misconception.name}")
        print(f" Why it happens: {misconception.description}")
        print(f" Tutor hint: {misconception.remediation_hint}")
    if not shown and active:
        print("\n Focus: let's rebuild this mechanism one step at a time.")


def run_guided_scaffolding(coordinator, question_service, concept, curr_q, student):
    """
    Tier 3 Scaffolding: Walks the student through atomic micro-steps
    until every micro-step in the walkthrough is complete.

    Returns a result dict on completion, None if there is nothing to scaffold,
    or the sentinel strings "QUIT"/"RESTART".
    """
    print_header(f"GUIDED STEP-BY-STEP SCAFFOLDING: {concept.title.upper()}")
    print("Don't worry! That's what a personal tutor is for.")
    print("Let's build this concept together one simple step at a time.\n")

    steps = curr_q.scaffold_steps
    if not steps:
        print(f"Reference Solution:\n{curr_q.canonical_answer}\n")
        print(f"Explanation:\n{curr_q.explanation}\n")
        return None

    for step in steps:
        print("-" * 60)
        print(f"MICRO-STEP {step.step_number} of {len(steps)}:")
        print(f"  {step.prompt}")
        if step.hint:
            print(f"  (Tip: {step.hint})")

        while True:
            s_ans = read_answer(f"\n{student.name}'s Step {step.step_number} Answer > ")

            if is_quit(s_ans):
                return "QUIT"
            if is_restart(s_ans):
                return "RESTART"

            s_eval = question_service.evaluate_scaffold_step(step, s_ans)
            if s_eval.is_correct:
                print(f"  [OK] Correct! {step.explanation}")
                break
            print(f"  [Hint]: Expected: '{step.expected_answer}'")
            print(f"  Let's type '{step.expected_answer}' to confirm this step.")

    print("\n" + "=" * 70)
    print(" [*** GUIDED WALKTHROUGH COMPLETE! ***]")
    print(f" You have successfully assembled the full mechanism for {concept.title}!")
    print(" This was guided practice, so let's reinforce it with another question.")
    print("=" * 70)

    # Award mastery for completing the guided scaffolding.
    res = coordinator.process_student_eval(
        concept_id=concept.id,
        question=curr_q.prompt,
        student_response="[Completed Guided Scaffolding Walkthrough]",
        score=0.85,
        detected_misconceptions=[],
        feedback="Completed the guided walkthrough; mastery evidence recorded."
    )
    return res


def build_coordinator(
    student: StudentProfile, repository: Optional[StudentRepository] = None
) -> TutorCoordinator:
    return TutorCoordinator(
        student_profile=student,
        concepts_file=CONCEPTS_FILE,
        knowledge_file=KNOWLEDGE_FILE,
        mastery_threshold=0.70,
        repository=repository,
    )


def main():
    configure_console()
    print_header("WELCOME TO YOUR ADAPTIVE AI TUTOR")
    print("This tutor doesn't just grade -- it actively teaches.")
    print("If you struggle, it breaks the challenge down into micro-steps")
    print("and guides you line-by-line until you can complete the mechanism step by step.")
    print("Type 'quit' or 'exit' at any prompt to finish.\n")

    try:
        raw_name = input("Enter your name (press Enter for 'Student'): ")
    except (KeyboardInterrupt, EOFError):
        print("\nSession ended.")
        return

    user_name = raw_name.strip()
    if is_quit(user_name):
        print("\nSession ended.")
        return
    if not user_name:
        user_name = "Student"

    db_path = get_records_db_path()
    repo = StudentRepository(db_path) if db_path else None
    student_id = f"stu_{user_name.lower().replace(' ', '_')}"
    existing_profile = repo.load_profile(student_id) if repo else None

    if existing_profile:
        student = existing_profile
        is_returning = True
    else:
        student = StudentProfile(
            student_id=student_id,
            name=user_name,
            target_goal="Master Python from fundamentals",
            explanation_preference="analogy_heavy"
        )
        if repo:
            repo.save_profile(student)
        is_returning = False

    try:
        coordinator = build_coordinator(student, repository=repo)
        question_service = QuestionService(QUESTIONS_FILE)
        misconception_catalog = {
            (concept_id, misconception.id)
            for concept_id, concept in coordinator.graph_service.concepts.items()
            for misconception in concept.misconceptions
        }
        question_service.validate(
            concept_ids=set(coordinator.graph_service.concepts),
            misconception_catalog=misconception_catalog,
        )
    except (OSError, ValueError) as exc:
        print(f"\nThe tutor could not start: {exc}")
        return

    if is_returning:
        print_header(f"WELCOME BACK, {student.name.upper()}!")
        print("  Resuming your saved learning progress from persistent disk storage.")
        cursor_data = repo.load_session_cursor(student.student_id) if repo else {}
        question_indexes = cursor_data.get("question_indexes", {})
    else:
        question_indexes = {}

    print_curriculum_dashboard(coordinator)

    def restart_session() -> TutorCoordinator:
        print("\n" + "=" * 70)
        print(" [RESTARTING TUTORING SESSION FROM SCRATCH...]".center(70))
        print("=" * 70 + "\n")
        question_indexes.clear()
        if repo:
            repo.reset_student(student.student_id)
        fresh_student = StudentProfile(
            student_id=student.student_id,
            name=student.name,
            target_goal=student.target_goal,
            explanation_preference=student.explanation_preference
        )
        if repo:
            repo.save_profile(fresh_student)
        fresh = build_coordinator(fresh_student, repository=repo)
        print_curriculum_dashboard(fresh)
        return fresh

    try:
        while True:
            recommendation = coordinator.recommend_next_action()
            target_cid = recommendation.target_concept_id
            concept = coordinator.graph_service.concepts[target_cid]

            if recommendation.action_type == "COMPLETE":
                print_header("CONGRATULATIONS! ALL CURRICULUM CONCEPTS MASTERED!")
                print("You have successfully demonstrated mastery across all foundational units.")
                break

            if recommendation.action_type == "INTRODUCE":
                print_header(f"NEW CONCEPT UNLOCKED: {concept.title.upper()}")
                lesson = coordinator.get_lesson_context(target_cid)
                print("\nLESSON BITE:")
                for chunk in lesson["verified_content_chunks"]:
                    print(f"  {chunk}\n")
                print(f"Ground Truth Source: {lesson['citations']}")
                print("\nLet's test your understanding with a diagnostic question.")

            elif recommendation.action_type == "REMEDIATE":
                print_header(f"TARGETED REMEDIATION: {concept.title.upper()}")
                print_misconception_briefing(
                    coordinator, target_cid, recommendation.active_misconceptions
                )

            elif recommendation.action_type == "PRACTICE":
                print(f"\n[Continuing Practice for: {concept.title}]")

            # Fetch questions for this concept.
            c_questions = question_service.get_questions_for_concept(target_cid)
            curr_idx = question_indexes.get(target_cid, 0)

            if curr_idx < len(c_questions):
                curr_q = c_questions[curr_idx]
                print(f"\nTUTOR QUESTION {curr_idx + 1} of {len(c_questions)}:")
            else:
                curr_q = c_questions[-1]
                print(
                    f"\n[REVIEW ROUND] You have finished all {len(c_questions)} unique "
                    "question(s) for this concept."
                )
                print(
                    "Mastery is built from repeated evidence, so this is another practice "
                    f"attempt. You need {coordinator.mastery_threshold * 100:.0f}% to unlock the next topic."
                )

            print(f"  {curr_q.prompt}")
            if curr_q.hint:
                print(f"  (Tip: {curr_q.hint})")

            user_response = read_answer(f"\n{student.name}'s Answer > ")

            if is_quit(user_response):
                break

            if is_restart(user_response):
                coordinator = restart_session()
                continue

            # Evaluate.
            eval_res = question_service.evaluate_main_question(curr_q, user_response)

            # Process assessment and update mastery.
            result = coordinator.process_student_eval(
                concept_id=target_cid,
                question=curr_q.prompt,
                student_response=user_response,
                score=eval_res.score,
                detected_misconceptions=eval_res.detected_misconceptions,
                feedback=eval_res.feedback
            )

            # Display educational feedback and explanation.
            print("\n" + "-" * 70)
            print(" EVALUATOR FEEDBACK & EXPLANATION")
            print("-" * 70)

            if eval_res.is_correct:
                print(f" Result: CORRECT (Score: {eval_res.score * 100:.0f}%)")
                print(f" Feedback: {eval_res.feedback}\n")
                print(" HOW IT WORKS:")
                for line in eval_res.explanation.split("\n"):
                    print(f"   {line}")
                question_indexes[target_cid] = curr_idx + 1
            else:
                label = "PARTIALLY CORRECT" if eval_res.score > 0 else "NEEDS WORK"
                print(f" Result: {label} (Score: {eval_res.score * 100:.0f}%)")
                if eval_res.diagnosis:
                    print(f" Diagnosis: {eval_res.diagnosis}\n")

                # Targeted remediation happens right away, on the same turn as the
                # mistake, instead of waiting for a later recommendation.
                if eval_res.detected_misconceptions:
                    print(" TARGETED MISCONCEPTION REMEDIATION")
                    print_misconception_briefing(
                        coordinator, target_cid, eval_res.detected_misconceptions
                    )
                    print()

                print(" REFERENCE CORRECT ANSWER:")
                print(f"   {eval_res.canonical_answer}\n")

                print(" STEP-BY-STEP EXPLANATION:")
                for line in eval_res.explanation.split("\n"):
                    print(f"   {line}")

                # Offer a follow-up transfer challenge.
                followup_succeeded = False
                if eval_res.has_followup and eval_res.followup_question:
                    followup = eval_res.followup_question
                    print("\n" + "=" * 70)
                    print(" FOLLOW-UP TRANSFER CHALLENGE")
                    print("=" * 70)
                    print("Now apply this mechanism to a fresh scenario to prove understanding:\n")
                    print(f"  {followup.prompt}")
                    if followup.hint:
                        print(f"  (Tip: {followup.hint})")

                    f_response = read_answer(f"\n{student.name}'s Follow-up Answer > ")

                    if is_quit(f_response):
                        break

                    if is_restart(f_response):
                        coordinator = restart_session()
                        continue

                    f_eval = question_service.evaluate_followup(curr_q, f_response)
                    print("\n" + "-" * 50)
                    if f_eval.is_correct:
                        print(" Result: CORRECT on Follow-Up Challenge!")
                        print(f" Feedback: {f_eval.feedback}")
                        f_res = coordinator.process_student_eval(
                            concept_id=target_cid,
                            question=followup.prompt,
                            student_response=f_response,
                            score=1.0,
                            detected_misconceptions=[],
                            feedback="Solved transfer question successfully!"
                        )
                        result = f_res
                        question_indexes[target_cid] = curr_idx + 1
                        followup_succeeded = True
                    else:
                        print(" Result: Still Needs Practice")
                        print(f" Expected: {f_eval.canonical_answer}")

                # If the student failed both the main question and the follow-up,
                # trigger Tier 3 guided scaffolding (never leave them stuck).
                if not followup_succeeded:
                    scaffold_res = run_guided_scaffolding(
                        coordinator, question_service, concept, curr_q, student
                    )
                    if scaffold_res == "QUIT":
                        break
                    if scaffold_res == "RESTART":
                        coordinator = restart_session()
                        continue
                    if scaffold_res:
                        result = scaffold_res
                        question_indexes[target_cid] = curr_idx + 1

            threshold_pct = coordinator.mastery_threshold * 100
            print(f"\n Updated Mastery on '{concept.title}': {result['new_mastery'] * 100:.1f}%")
            print(f" Statistical Confidence: {result['confidence'] * 100:.1f}%")
            if result["new_mastery"] < coordinator.mastery_threshold:
                print(
                    f" Mastery target is {threshold_pct:.0f}% - keep practising this concept "
                    "to unlock the next topic."
                )

            # Check if a new concept was just unlocked.
            if target_cid in result["frontier_mastered"]:
                print(f"\n[*** MASTERY VERIFIED! ***] You have mastered: {concept.title} (>= {threshold_pct:.0f}%)")
                new_ready = [cid for cid in result["frontier_ready"] if cid != target_cid]
                if new_ready:
                    next_title = coordinator.graph_service.concepts[new_ready[0]].title
                    print(f"[UNLOCKED] '{next_title}' is now READY to be learned!")

            print_curriculum_dashboard(coordinator)
            if repo:
                repo.save_session_cursor(student.student_id, question_indexes, {}, target_cid)
            wait_for_enter()

    except (SessionExit, KeyboardInterrupt):
        pass

    print_header("SESSION SUMMARY")
    print_curriculum_dashboard(coordinator)
    print("\nGreat progress today! See you next session.\n")


if __name__ == "__main__":
    main()
