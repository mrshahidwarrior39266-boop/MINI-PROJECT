"""
End-to-End Live Integration Tests for ArchaLearn Codex Web Server.
Verifies all static assets and REST API endpoints over live HTTP connections.
"""
import json
import threading
import urllib.request
import urllib.parse
from http.server import HTTPServer
import pytest

from app.server import ThreadedHTTPServer, TutorHTTPRequestHandler, STATE


@pytest.fixture(scope="module")
def live_server():
    """Start the Codex HTTP server on a random free OS port."""
    server = ThreadedHTTPServer(("127.0.0.1", 0), TutorHTTPRequestHandler)
    host, port = server.server_address
    base_url = f"http://{host}:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield base_url

    server.shutdown()
    server.server_close()


def test_static_html(live_server):
    with urllib.request.urlopen(f"{live_server}/") as resp:
        assert resp.status == 200
        content = resp.read().decode("utf-8")
        assert "Codex Tutor" in content
        assert "Intelligent Tutoring System" in content
        assert "view-home" in content
        assert "view-lessons" in content
        assert "view-plan" in content
        assert "animation-stage-viewport" in content


def test_static_css_and_js(live_server):
    for asset in ["styles.css", "animations.js", "app.js"]:
        with urllib.request.urlopen(f"{live_server}/{asset}") as resp:
            assert resp.status == 200
            assert len(resp.read()) > 0


def test_api_status(live_server):
    with urllib.request.urlopen(f"{live_server}/api/status") as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["system"] == "ArchaLearn Intelligent Tutoring System"
        assert "active_student" in data
        assert "ledger_audit" in data
        assert data["ledger_audit"]["verified"] is True


def test_api_curriculum(live_server):
    with urllib.request.urlopen(f"{live_server}/api/curriculum") as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["total_concepts"] == 8
        assert len(data["concepts"]) == 8
        cids = [c["id"] for c in data["concepts"]]
        assert "py.variables" in cids
        assert "py.functions" in cids


def test_api_session_plan(live_server):
    with urllib.request.urlopen(f"{live_server}/api/session-plan?n=10") as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["target_total_items"] == 10
        assert data["counts"]["review"] == 3
        assert data["counts"]["frontier"] == 6
        assert data["counts"]["synthesis"] == 1
        assert len(data["items"]) == 10


def test_api_lessons_all_and_single(live_server):
    with urllib.request.urlopen(f"{live_server}/api/lessons") as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert len(data["lessons"]) == 8

    # Test single lesson for functions
    with urllib.request.urlopen(f"{live_server}/api/lessons/py.functions") as resp:
        assert resp.status == 200
        lesson = json.loads(resp.read().decode("utf-8"))
        assert lesson["concept_id"] == "py.functions"
        assert "Call Stacks" in lesson["title"]
        assert "call_stack" in lesson["animation_id"]


def test_api_evaluate(live_server):
    req_data = json.dumps({
        "concept_id": "py.variables",
        "student_answer": "temp = a; a = b; b = temp using intermediate temporary storage to prevent overwriting",
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{live_server}/api/evaluate",
        data=req_data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "is_correct" in data
        assert "feedback" in data
        assert "audit_block_hash" in data
        assert isinstance(data["cited_chunk_ids"], list)


def test_api_memory_state(live_server):
    with urllib.request.urlopen(f"{live_server}/api/memory-state") as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "variables" in data
        assert len(data["variables"]) >= 4
        assert len(data["swap_movie_steps"]) == 3
