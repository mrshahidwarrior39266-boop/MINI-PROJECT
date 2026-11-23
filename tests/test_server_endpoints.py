"""
Unit tests for the ArchaLearn Codex HTTP Server and REST API endpoints.
"""
import json
import pytest
from app.server import STATE, LESSONS_CATALOG
from app.models.student import StudentProfile


def test_server_status():
    frontier = STATE.coordinator.get_frontier()
    assert len(STATE.graph_service.concepts) == 8
    assert STATE.active_profile is not None
    assert frontier is not None


def test_lessons_catalog_completeness():
    # Every concept must have an authoritative lesson defined
    concept_ids = set(STATE.graph_service.concepts.keys())
    assert len(LESSONS_CATALOG) == 8
    for cid in concept_ids:
        assert cid in LESSONS_CATALOG, f"Missing lesson for concept {cid}"
        lesson = LESSONS_CATALOG[cid]
        assert lesson["title"]
        assert lesson["theory"]
        assert lesson["code_example"]
        assert "analogy" in lesson
        assert lesson["misconceptions"]
        assert lesson["diagnostic_prompt"]
        assert lesson["animation_id"]


def test_session_plan_generation():
    mastery_map = STATE.repository.load_mastery_map(STATE.active_profile.student_id)
    plan = STATE.curriculum_planner.generate_daily_plan(
        student_profile=STATE.active_profile,
        mastery_map=mastery_map,
        target_total_items=10,
    )
    assert len(plan.all_scheduled_items) == 10
    assert len(plan.review_items) == 3
    assert len(plan.frontier_items) == 6
    assert len(plan.synthesis_items) == 1
    assert "30% Review" in plan.ratio_summary


def test_synthesis_challenges_load():
    with open("app/data/synthesis_challenges.json", "r", encoding="utf-8") as f:
        challenges = json.load(f)
    assert len(challenges) == 6
    for c in challenges:
        assert "id" in c
        assert "title" in c
        assert "required_concept_ids" in c
        assert "prompt" in c
        assert "canonical_answer" in c
