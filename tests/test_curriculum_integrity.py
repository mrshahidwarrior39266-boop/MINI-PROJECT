"""Curriculum data invariants that must hold before the tutor can start."""
import json
from pathlib import Path

import pytest

from app.models.concept import Concept
from app.services.concept_graph import ConceptGraphError, ConceptGraphService
from app.services.knowledge_base import KnowledgeBaseService
from app.services.question_service import QuestionService

ROOT = Path(__file__).resolve().parent.parent
CONCEPTS = ROOT / "app" / "data" / "python_concepts.json"
KNOWLEDGE = ROOT / "app" / "data" / "python_knowledge.json"
QUESTIONS = ROOT / "app" / "data" / "curriculum_questions.json"


@pytest.fixture(scope="module")
def graph():
    return ConceptGraphService(CONCEPTS)


@pytest.fixture(scope="module")
def knowledge():
    return KnowledgeBaseService(KNOWLEDGE)


@pytest.fixture(scope="module")
def questions():
    return QuestionService(QUESTIONS)


def test_every_concept_has_lesson_material_and_questions(graph, knowledge, questions):
    for concept_id in graph.concepts:
        assert knowledge.get_chunks_for_concept(concept_id), concept_id
        assert questions.get_questions_for_concept(concept_id), concept_id


def test_question_data_passes_startup_validation(graph, questions):
    catalog = {
        (concept_id, misconception.id)
        for concept_id, concept in graph.concepts.items()
        for misconception in concept.misconceptions
    }
    questions.validate(set(graph.concepts), catalog)


def test_every_question_has_followup_and_scaffold(questions):
    for question in questions.questions.values():
        assert question.followup is not None, question.id
        assert question.scaffold_steps, question.id


def test_duplicate_question_id_is_rejected(tmp_path):
    data = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    data.append(data[0])
    duplicate = tmp_path / "questions.json"
    duplicate.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate question id"):
        QuestionService(duplicate)


def test_duplicate_concept_id_is_rejected():
    graph = ConceptGraphService()
    concept = Concept(id="dup", subject="test", title="A", description="desc")
    graph.add_concept(concept)
    with pytest.raises(ConceptGraphError, match="Duplicate concept ID"):
        graph.add_concept(concept)


def test_missing_knowledge_chunk_is_rejected(knowledge):
    with pytest.raises(ValueError, match="Missing knowledge chunks"):
        knowledge.validate({"py.variables", "py.not_a_real_concept"})


def test_empty_curriculum_is_rejected():
    with pytest.raises(ConceptGraphError, match="No concepts were loaded"):
        ConceptGraphService().validate_graph_integrity()
