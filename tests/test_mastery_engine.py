import pytest
from app.models.student import StudentProfile
from app.services.student_state import StudentStateService


def test_initial_mastery():
    profile = StudentProfile(student_id="stu_001", name="Alice")
    state_service = StudentStateService(profile)
    
    mastery = state_service.get_or_create_mastery("py.variables")
    assert mastery.mastery == 0.0
    assert mastery.confidence == 0.0
    assert mastery.attempts_count == 0


def test_evidence_update_and_confidence_growth():
    profile = StudentProfile(student_id="stu_001", name="Alice")
    state_service = StudentStateService(profile)
    
    # First correct answer (score = 1.0)
    record, log = state_service.record_assessment(
        concept_id="py.variables",
        question="What does x = 5 do in Python?",
        student_response="Assigns 5 to label x",
        score=1.0,
        feedback="Accurate description of name binding."
    )
    
    assert record.mastery > 0.0
    assert record.confidence > 0.0
    assert record.attempts_count == 1
    assert record.success_count == 1
    assert log.is_correct is True


def test_misconception_penalty():
    profile = StudentProfile(student_id="stu_001", name="Alice")
    state_service = StudentStateService(profile)
    
    # Student scores 0.5 with a misconception
    record, log = state_service.record_assessment(
        concept_id="py.variables",
        question="Why does x = x + 1 work?",
        student_response="It links x permanently to itself.",
        score=0.4,
        detected_misconceptions=["variable_permanent_link"],
        feedback="Notice that this evaluates once, not a live binding."
    )
    
    assert "variable_permanent_link" in record.active_misconceptions
    # The penalty should keep the mastery low
    assert record.mastery < 0.25
