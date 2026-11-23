"""
End-to-End Live Integration Tests for ArchaLearn Codex Web Server.
Verifies all static assets and REST API endpoints over live HTTP connections.
"""
import json
import threading
import urllib.error
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


def _json_request(url, payload=None, raw=None):
    """Issue a JSON request and return (status, parsed body) even on 4xx/5xx."""
    if raw is not None:
        data = raw
    elif payload is not None:
        data = json.dumps(payload).encode("utf-8")
    else:
        data = None
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def test_api_questions_and_unknown_concept(live_server):
    status, data = _json_request(f"{live_server}/api/questions/py.variables")
    assert status == 200
    assert data["total_questions"] >= 3
    assert all("prompt" in q and "id" in q for q in data["questions"])

    status, data = _json_request(f"{live_server}/api/questions/nope")
    assert status == 404
    assert data["error"] is True


def test_api_unknown_routes_return_json_404(live_server):
    for path in ("/api/nope", "/api/rag/nope", "/api/questions"):
        status, data = _json_request(f"{live_server}{path}")
        assert status == 404
        assert data["error"] is True
        assert "message" in data


def test_api_audit_trail(live_server):
    status, data = _json_request(f"{live_server}/api/audit-trail")
    assert status == 200
    assert data["verified"] is True
    assert isinstance(data["recent_evaluations"], list)
    assert data["history_count"] >= len(data["recent_evaluations"])


def test_api_rag_search_shape(live_server):
    status, data = _json_request(f"{live_server}/api/rag/search?q=assignment")
    assert status == 200
    assert data["results_count"] == len(data["results"])
    assert data["results_count"] > 0
    first = data["results"][0]
    for key in ("chunk_id", "concept_id", "source_title", "content", "similarity"):
        assert key in first
    assert 0.0 <= first["similarity"] <= 1.0


def test_api_rag_search_rejects_bad_k(live_server):
    for k in ("0", "abc", "21"):
        status, data = _json_request(
            f"{live_server}/api/rag/search?q=assignment&k={k}"
        )
        assert status == 400
        assert data["error"] is True


def test_api_session_plan_rejects_bad_n(live_server):
    for n in ("abc", "0", "51"):
        status, data = _json_request(f"{live_server}/api/session-plan?n={n}")
        assert status == 400
        assert data["error"] is True


def test_api_rag_ingest_and_retrieve(live_server):
    doc = (
        "# Sentinel Flags\n\n"
        "A sentinel flag is a boolean variable that tells a while loop to stop. "
        "Update the flag and use break to terminate the loop safely.\n"
    )
    status, data = _json_request(
        f"{live_server}/api/rag/ingest",
        {"filename": "qa_regression_notes.md", "content": doc},
    )
    assert status == 200
    assert data["success"] is True
    assert data["chunks_extracted"] >= 1
    assert data["linked_concepts"]

    status, data = _json_request(
        f"{live_server}/api/rag/search?q=sentinel%20flag"
    )
    assert status == 200
    assert any("sentinel" in result["content"].lower() for result in data["results"])


def test_api_evaluate_validation(live_server):
    status, data = _json_request(
        f"{live_server}/api/evaluate",
        {"concept_id": "py.nope", "student_answer": "x"},
    )
    assert status == 404
    assert data["error"] is True

    status, data = _json_request(
        f"{live_server}/api/evaluate",
        {"concept_id": "py.variables", "student_answer": 123},
    )
    assert status == 400
    assert data["error"] is True

    status, data = _json_request(
        f"{live_server}/api/evaluate", raw=b"{not valid json"
    )
    assert status == 400
    assert data["error"] is True

    status, data = _json_request(
        f"{live_server}/api/evaluate", payload=[1, 2, 3]
    )
    assert status == 400
    assert data["error"] is True


def test_api_evaluate_records_one_audit_entry(live_server):
    _, before = _json_request(f"{live_server}/api/audit-trail")
    q_status, q_data = _json_request(f"{live_server}/api/questions/py.variables")
    assert q_status == 200
    question = q_data["questions"][0]

    status, evaluation = _json_request(
        f"{live_server}/api/evaluate",
        {
            "concept_id": "py.variables",
            "student_answer": (
                "x = x + 1 evaluates the right side first, then binds "
                "the new value back to the variable x."
            ),
            "question_prompt": question["prompt"],
        },
    )
    assert status == 200
    assert "score" in evaluation

    _, after = _json_request(f"{live_server}/api/audit-trail")
    assert after["history_count"] == before["history_count"] + 1
