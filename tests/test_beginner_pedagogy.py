"""
Automated Tests for Beginner Pedagogy & Real-World Physical Analogies.
"""
import json
from pathlib import Path

import pytest

from app.models.concept import Concept
from app.models.student import StudentProfile
from app.services.beginner_pedagogy import BeginnerPedagogyService
from app.services.tutor_coordinator import TutorCoordinator

DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "data"
CONCEPTS_FILE = DATA_DIR / "python_concepts.json"
KNOWLEDGE_FILE = DATA_DIR / "python_knowledge.json"


@pytest.fixture
def pedagogy():
    return BeginnerPedagogyService()


def test_all_8_concepts_have_beginner_analogies(pedagogy):
    raw_concepts = json.loads(CONCEPTS_FILE.read_text(encoding="utf-8"))
    assert len(raw_concepts) == 8

    for c in raw_concepts:
        cid = c["id"]
        analogy = pedagogy.get_analogy(cid)
        assert analogy is not None, f"Concept '{cid}' missing beginner analogy"
        assert "real_world_analogy" in analogy
        assert len(analogy["real_world_analogy"]) > 5
        assert "plain_english_concept" in analogy
        assert len(analogy["plain_english_concept"]) > 10
        assert "human_vs_computer_trap" in analogy
        assert len(analogy["human_vs_computer_trap"]) > 10
        assert "mental_movie" in analogy
        assert len(analogy["mental_movie"]) > 10


def test_format_beginner_briefing_renders_physical_model(pedagogy):
    briefing = pedagogy.format_beginner_briefing("py.variables")
    assert "ZERO-KNOWLEDGE INTUITION" in briefing
    assert "Cardboard Boxes" in briefing
    assert "ACTION ARROW" in briefing
    assert "3-Second Mental Movie" in briefing


def test_coordinator_integrates_beginner_pedagogy():
    student = StudentProfile(student_id="stu_beginner", name="Newbie")
    coordinator = TutorCoordinator(
        student_profile=student,
        concepts_file=CONCEPTS_FILE,
        knowledge_file=KNOWLEDGE_FILE,
    )

    # 1. Lesson context includes beginner mental model
    ctx = coordinator.get_lesson_context("py.variables")
    assert "beginner_mental_model" in ctx
    assert ctx["beginner_mental_model"]["real_world_analogy"] == "Cardboard Boxes with Sticky Note Name-Tags"

    # 2. Formatted briefing is accessible
    briefing = coordinator.get_beginner_briefing("py.variables")
    assert "Cardboard Boxes" in briefing
    assert "x = x + 1" in briefing
