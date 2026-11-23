"""Tests for the Mastery Reporter & Verifiable Student Transcript Service."""
from pathlib import Path
import pytest

from app.models.student import StudentProfile
from app.services.tutor_coordinator import TutorCoordinator
from app.services.mastery_reporter import MasteryReporter

ROOT = Path(__file__).resolve().parent.parent
CONCEPTS_FILE = ROOT / "app" / "data" / "python_concepts.json"
KNOWLEDGE_FILE = ROOT / "app" / "data" / "python_knowledge.json"


@pytest.fixture
def coordinator():
    student = StudentProfile(
        student_id="test_student_01",
        name="Alex Turing",
        target_goal="Become a Python Pro",
        explanation_preference="analogy_heavy",
    )
    return TutorCoordinator(
        student_profile=student,
        concepts_file=CONCEPTS_FILE,
        knowledge_file=KNOWLEDGE_FILE,
        mastery_threshold=0.85,
    )


def test_compute_audit_hash(coordinator):
    hash1 = MasteryReporter.compute_audit_hash(coordinator)
    assert isinstance(hash1, str)
    assert len(hash1) == 16

    # Deterministic check
    hash2 = MasteryReporter.compute_audit_hash(coordinator)
    assert hash1 == hash2

    # Change when assessment occurs
    coordinator.process_student_eval(
        concept_id="py.variables",
        question="What is x = 5?",
        student_response="Assign 5 to x",
        score=1.0,
        detected_misconceptions=[],
        feedback="Correct!",
    )
    hash3 = MasteryReporter.compute_audit_hash(coordinator)
    assert hash3 != hash1


def test_generate_json_report(coordinator):
    coordinator.process_student_eval(
        concept_id="py.variables",
        question="What is x = 5?",
        student_response="Assign 5 to x",
        score=1.0,
        detected_misconceptions=[],
        feedback="Correct!",
    )
    report = MasteryReporter.generate_json_report(coordinator)
    assert report["student"]["name"] == "Alex Turing"
    assert report["student"]["id"] == "test_student_01"
    assert "TRANSCRIPT-" in report["transcript_id"]
    assert report["curriculum_summary"]["total_concepts"] == 8
    assert report["curriculum_summary"]["total_assessments_logged"] == 1
    assert len(report["concepts"]) == 8
    assert len(report["verification_audit_hash"]) == 16


def test_generate_markdown_report(coordinator):
    # Record one evaluation with a misconception to test misconception reporting
    coordinator.process_student_eval(
        concept_id="py.variables",
        question="What is x = x + 1?",
        student_response="It's impossible in math",
        score=0.2,
        detected_misconceptions=["confuse_assign_equals"],
        feedback="In Python, = is assignment.",
    )
    md = MasteryReporter.generate_markdown_report(coordinator)
    assert "# Student Mastery Transcript & Competency Portfolio" in md
    assert "Alex Turing" in md
    assert "TRANSCRIPT-" in md
    assert "confuse_assign_equals" in md
    assert "Integrity Guarantee" in md
    assert "| Concept | Status | Mastery |" in md


def test_export_report_to_file(coordinator, tmp_path):
    exported_file = MasteryReporter.export_report_to_file(coordinator, output_dir=tmp_path)
    assert exported_file.exists()
    assert exported_file.suffix == ".md"
    content = exported_file.read_text(encoding="utf-8")
    assert "Alex Turing" in content
    assert "test_student_01" in exported_file.name
