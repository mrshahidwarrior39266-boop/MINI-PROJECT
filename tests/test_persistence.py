import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.models.student import StudentProfile
from app.services.student_repository import StudentRepository
from app.services.student_state import StudentStateService
from app.services.tutor_coordinator import TutorCoordinator

DATA_DIR = Path(__file__).parent.parent / "app" / "data"
CONCEPTS_FILE = DATA_DIR / "python_concepts.json"
KNOWLEDGE_FILE = DATA_DIR / "python_knowledge.json"


def test_repository_profile_crud():
    with TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_records.db"
        repo = StudentRepository(db_path)

        profile = StudentProfile(
            student_id="stu_test_user",
            name="Test User",
            target_goal="Learn Python",
            explanation_preference="analogy_heavy"
        )
        repo.save_profile(profile)

        loaded = repo.load_profile("stu_test_user")
        assert loaded is not None
        assert loaded.name == "Test User"
        assert loaded.student_id == "stu_test_user"

        all_profiles = repo.list_profiles()
        assert len(all_profiles) == 1
        assert all_profiles[0].student_id == "stu_test_user"


def test_state_service_persistence_and_reload():
    with TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_records.db"
        repo = StudentRepository(db_path)

        alice = StudentProfile(
            student_id="stu_alice",
            name="Alice",
            target_goal="Fundamentals"
        )
        state_service_1 = StudentStateService(alice, repository=repo)

        # 1. Record an assessment
        rec, log = state_service_1.record_assessment(
            concept_id="py.variables",
            question="What is x = 5?",
            student_response="Assigns 5 to x",
            score=1.0,
            detected_misconceptions=[],
            feedback="Great!"
        )
        assert rec.mastery > 0.0
        original_mastery = rec.mastery

        # 2. Simulate process exit and reload in a brand new StateService instance
        state_service_2 = StudentStateService(alice, repository=repo)
        assert "py.variables" in state_service_2.mastery_map
        reloaded_mastery = state_service_2.mastery_map["py.variables"].mastery
        assert reloaded_mastery == original_mastery

        # Check logs reloaded
        assert len(state_service_2.assessment_history) == 1
        assert state_service_2.assessment_history[0].question_asked == "What is x = 5?"


def test_coordinator_resumes_student_session():
    with TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_records.db"
        repo = StudentRepository(db_path)

        student = StudentProfile(
            student_id="stu_bob",
            name="Bob"
        )

        # Session 1: Bob achieves 72.5% on Variables
        coord_1 = TutorCoordinator(
            student_profile=student,
            concepts_file=CONCEPTS_FILE,
            knowledge_file=KNOWLEDGE_FILE,
            mastery_threshold=0.70,
            repository=repo
        )

        # Simulate 3 successful exercises
        for i in range(3):
            coord_1.process_student_eval(
                concept_id="py.variables",
                question=f"Q{i}",
                student_response=f"A{i}",
                score=1.0,
                detected_misconceptions=[],
                feedback="Correct"
            )

        f1 = coord_1.get_frontier()
        assert "py.variables" in f1.mastered
        assert "py.data_types" in f1.ready

        # Save cursor
        repo.save_session_cursor(student.student_id, {"py.variables": 3}, {}, "py.data_types")

        # Session 2: Fresh coordinator in a new session
        coord_2 = TutorCoordinator(
            student_profile=student,
            concepts_file=CONCEPTS_FILE,
            knowledge_file=KNOWLEDGE_FILE,
            mastery_threshold=0.70,
            repository=repo
        )

        f2 = coord_2.get_frontier()
        assert "py.variables" in f2.mastered
        assert "py.data_types" in f2.ready

        cursor = repo.load_session_cursor(student.student_id)
        assert cursor["question_indexes"] == {"py.variables": 3}
        assert cursor["last_active_concept"] == "py.data_types"

        # Next recommended action should immediately be INTRODUCE 'py.data_types'
        next_goal = coord_2.recommend_next_action()
        assert next_goal.target_concept_id == "py.data_types"
        assert next_goal.action_type == "INTRODUCE"


def test_reset_student():
    with TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_records.db"
        repo = StudentRepository(db_path)

        student = StudentProfile(student_id="stu_charlie", name="Charlie")
        repo.save_profile(student)

        service = StudentStateService(student, repository=repo)
        service.record_assessment("py.variables", "Q", "A", 1.0)
        assert len(repo.load_mastery_map("stu_charlie")) == 1

        # Reset student
        repo.reset_student("stu_charlie")
        assert repo.load_profile("stu_charlie") is None
        assert len(repo.load_mastery_map("stu_charlie")) == 0
        assert len(repo.load_assessment_history("stu_charlie")) == 0
