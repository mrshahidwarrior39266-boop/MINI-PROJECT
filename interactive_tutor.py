"""
Interactive Tutor CLI:
Allows a real student to engage in a live Socratic tutoring session.
You type answers, the system diagnoses your understanding, updates your mastery,
and unlocks new concepts dynamically as you prove competency.
"""
import sys
from pathlib import Path

from app.models.student import StudentProfile
from app.services.tutor_coordinator import TutorCoordinator
from app.services.evaluator import HeuristicEvaluator

DATA_DIR = Path(__file__).parent / "app" / "data"
CONCEPTS_FILE = DATA_DIR / "python_concepts.json"
KNOWLEDGE_FILE = DATA_DIR / "python_knowledge.json"


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

        misc = f" [! {len(mastery.active_misconceptions)} bugs]" if mastery.active_misconceptions else ""
        print(f"  {concept.title:<36} | {render_progress_bar(mastery.mastery)} | {status:<11}{misc}")
    print("-" * 70)


REMEDIATION_QUESTION_BANK = {
    "variable_permanent_link": {
        "q": "Let's test with fresh variables:\n   score1 = 50\n   score2 = score1\n   score1 = 100\nWhat is the value of 'score2', and why?",
        "context": "Remember the snapshot rule: what was score1 at the moment score2 was assigned?"
    },
    "confuse_assign_equals": {
        "q": "If count = 3, what does 'count = count + 2' do? What is the new value of count?",
        "context": "Calculate the right-hand side first, then store the result into count."
    }
}

QUESTION_BANK = {
    "py.variables": [
        {
            "q": "In Python, what does the expression 'x = x + 1' mean, and why is it not an algebraic impossibility?",
            "context": "Think about the order of execution: which side evaluates first, and what does '=' actually do?"
        },
        {
            "q": "Suppose we execute:\n   a = 10\n   b = a\n   a = 20\nWhat is the value of 'b' now, and why?",
            "context": "Does changing 'a' automatically change 'b', or did 'b' receive a copy/snapshot?"
        },
        {
            "q": "Write or describe the code to swap the values of two variables 'x' and 'y' without losing either value.",
            "context": "Hint: You might need a third temporary variable to hold one value."
        }
    ],
    "py.data_types": [
        {
            "q": "What will Python output for the expression: print(\"5\" + \"5\"), and why does it not output 10?",
            "context": "Pay attention to the quotation marks around the numbers."
        },
        {
            "q": "If you have age = '18' as a string, how do you convert it so you can perform math like age + 1?",
            "context": "Name the built-in function used for converting text to an integer."
        }
    ],
    "py.operators_expressions": [
        {
            "q": "What is the difference between '/' and '//' in Python 3? For example, what do 7 / 2 and 7 // 2 return?",
            "context": "One gives exact floating-point decimals, the other gives integer floor."
        }
    ]
}


def main():
    print_header("WELCOME TO YOUR ADAPTIVE AI TUTOR")
    print("This tutor doesn't just talk -- it listens, checks your answers for")
    print("specific misconceptions, tracks your mastery mathematically, and")
    print("unlocks the next concept ONLY after you prove you understand.")
    print("Type 'quit' or 'exit' at any prompt to finish.\n")

    user_name = input("Enter your name (press Enter for 'Student'): ").strip()
    if not user_name:
        user_name = "Student"

    student = StudentProfile(
        student_id=f"stu_{user_name.lower().replace(' ', '_')}",
        name=user_name,
        target_goal="Master Python from fundamentals",
        explanation_preference="analogy_heavy"
    )

    coordinator = TutorCoordinator(
        student_profile=student,
        concepts_file=CONCEPTS_FILE,
        knowledge_file=KNOWLEDGE_FILE,
        mastery_threshold=0.70
    )

    print_curriculum_dashboard(coordinator)

    question_indexes = {}

    while True:
        recommendation = coordinator.recommend_next_action()
        target_cid = recommendation.target_concept_id
        concept = coordinator.graph_service.concepts[target_cid]
        mastery = coordinator.student_service.get_or_create_mastery(target_cid)

        if recommendation.action_type == "COMPLETE":
            print_header("CONGRATULATIONS! ALL CURRICULUM CONCEPTS MASTERED!")
            print("You have successfully demonstrated mastery across all foundational units.")
            break

        # If introducing a concept for the first time
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
            print("Let's pause and clear up the concept before moving forward.")
            if mastery.active_misconceptions:
                misc_id = mastery.active_misconceptions[0]
                misc_obj = coordinator.graph_service.get_misconception(target_cid, misc_id)
                if misc_obj:
                    print(f"\n[Pedagogical Hint]: {misc_obj.remediation_hint}")
                    print(f"[Counter-Example]:\n{misc_obj.counter_example}\n")

        elif recommendation.action_type == "PRACTICE":
            print(f"\n[Continuing Practice for: {concept.title}]")

        # Pick question: if in REMEDIATE mode, choose a targeted Transfer Question
        if recommendation.action_type == "REMEDIATE" and mastery.active_misconceptions:
            active_bug = mastery.active_misconceptions[0]
            rem_data = REMEDIATION_QUESTION_BANK.get(active_bug)
            if rem_data:
                q_text = rem_data["q"]
                q_context = rem_data["context"]
            else:
                q_text = f"Explain why variables in Python are snapshots, not live links."
                q_context = "Use an example with two variables."
        else:
            # Pick from regular question bank
            q_list = QUESTION_BANK.get(target_cid, [])
            curr_idx = question_indexes.get(target_cid, 0)

            if curr_idx < len(q_list):
                q_data = q_list[curr_idx]
                q_text = q_data["q"]
                q_context = q_data.get("context", "")
            else:
                q_text = f"Explain the core rules and syntax of {concept.title} in your own words."
                q_context = "Provide an example showing how you would use it."

        print(f"\nTUTOR QUESTION:")
        print(f"  {q_text}")
        if q_context:
            print(f"  (Tip: {q_context})")

        # GET REAL USER INPUT
        try:
            user_response = input(f"\n{student.name}'s Answer > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSession ended.")
            break

        if not user_response or user_response.lower() in ["quit", "exit"]:
            print_header("SESSION SUMMARY")
            print_curriculum_dashboard(coordinator)
            print("\nGreat progress today! See you next session.\n")
            break

        # EVALUATE RESPONSE
        eval_res = HeuristicEvaluator.evaluate(concept, q_text, user_response)

        # PROCESS ASSESSMENT & UPDATE MASTERY
        result = coordinator.process_student_eval(
            concept_id=target_cid,
            question=q_text,
            student_response=user_response,
            score=eval_res.score,
            detected_misconceptions=eval_res.detected_misconceptions,
            feedback=eval_res.feedback
        )

        # FEEDBACK TO USER
        print("\n" + "-" * 50)
        print(" EVALUATOR FEEDBACK")
        print("-" * 50)
        if eval_res.is_correct:
            print(f" Result: CORRECT (Score: {eval_res.score * 100:.0f}%)")
            print(f" Feedback: {eval_res.feedback}")
            question_indexes[target_cid] = curr_idx + 1
        else:
            print(f" Result: NEEDS WORK (Score: {eval_res.score * 100:.0f}%)")
            print(f" Feedback: {eval_res.feedback}")
            if eval_res.remediation_hint:
                print(f" Hint: {eval_res.remediation_hint}")

        print(f"\n Updated Mastery on '{concept.title}': {result['new_mastery'] * 100:.1f}%")
        print(f" Statistical Confidence: {result['confidence'] * 100:.1f}%")

        # CHECK IF A NEW CONCEPT WAS JUST UNLOCKED
        if target_cid in result["frontier_mastered"]:
            print(f"\n[*** MASTERY VERIFIED! ***] You have mastered: {concept.title} (>= 70%)")
            new_ready = [cid for cid in result["frontier_ready"] if cid != target_cid]
            if new_ready:
                next_title = coordinator.graph_service.concepts[new_ready[0]].title
                print(f"[UNLOCKED] '{next_title}' is now READY to be learned!")

        print_curriculum_dashboard(coordinator)
        input("\n[Press Enter to continue to the next step...]")


if __name__ == "__main__":
    main()
