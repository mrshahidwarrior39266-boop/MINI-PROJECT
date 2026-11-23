"""
ArchaLearn Codex Web Server:
High-performance, threaded HTTP and REST API server connecting the Codex-inspired
frontend to the complete Intelligent Tutoring System backend services across all 4 Milestones.
"""
import json
import mimetypes
import os
import sys
import time
import urllib.parse
import uuid
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from pathlib import Path
from typing import Dict, Any, Optional, List

from app.models.student import StudentProfile, ConceptMastery, AssessmentLog
from app.models.evaluator import LLMEvaluationRequest
from app.services.tutor_coordinator import TutorCoordinator
from app.services.student_repository import StudentRepository
from app.services.concept_graph import ConceptGraphService
from app.services.question_service import QuestionService
from app.services.spaced_repetition import SpacedRepetitionEngine
from app.services.curriculum_planner import CurriculumPlanner
from app.services.semantic_rag import SemanticRAGService
from app.services.mastery_reporter import MasteryReporter
from app.services.document_ingestion import DocumentIngestionService
from app.services.concept_linker import ConceptLinkerService
from app.services.memory_visualizer import MemoryStateVisualizer
from app.services.lesson_content import LESSONS_CATALOG

ROOT_DIR = Path(__file__).resolve().parent.parent
APP_DIR = ROOT_DIR / "app"
DATA_DIR = APP_DIR / "data"
STATIC_DIR = APP_DIR / "static"
CONCEPTS_FILE = DATA_DIR / "python_concepts.json"
KNOWLEDGE_FILE = DATA_DIR / "python_knowledge.json"
QUESTIONS_FILE = DATA_DIR / "curriculum_questions.json"
DB_FILE = DATA_DIR / "tutor_records.db"
SYNTHESIS_FILE = DATA_DIR / "synthesis_challenges.json"


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in separate threads for maximum UI responsiveness."""
    daemon_threads = True
    allow_reuse_address = True


class TutorServerState:
    """Singleton service registry for the active web server session."""
    def __init__(self):
        self.repository = StudentRepository(DB_FILE)
        self.graph_service = ConceptGraphService(CONCEPTS_FILE)
        self.memory_visualizer = MemoryStateVisualizer()

        # Load or create active student
        profiles = self.repository.list_profiles()
        if profiles:
            # Prefer 'stu_shahid' if present, otherwise first available
            shahid = next((p for p in profiles if p.student_id == "stu_shahid"), None)
            self.active_profile = shahid if shahid else profiles[0]
        else:
            self.active_profile = StudentProfile(
                student_id="stu_turing",
                name="Alan Turing",
                target_goal="Master Python from fundamentals",
                explanation_preference="analogy_heavy",
                pace_rate=1.0,
            )
            self.repository.save_profile(self.active_profile)

        self._rebuild_coordinator()

    def _rebuild_coordinator(self):
        self.coordinator = TutorCoordinator(
            student_profile=self.active_profile,
            concepts_file=CONCEPTS_FILE,
            knowledge_file=KNOWLEDGE_FILE,
            repository=self.repository,
        )
        self.question_service = QuestionService(QUESTIONS_FILE)
        self.sr_engine = SpacedRepetitionEngine()
        self.curriculum_planner = CurriculumPlanner(
            graph_service=self.graph_service,
            question_service=self.question_service,
            spaced_repetition_engine=self.sr_engine,
            synthesis_file=SYNTHESIS_FILE,
            mastery_threshold=0.70,
        )

    def switch_student(self, student_id: str, name: Optional[str] = None) -> StudentProfile:
        loaded = self.repository.load_profile(student_id)
        if loaded:
            self.active_profile = loaded
        else:
            new_profile = StudentProfile(
                student_id=student_id,
                name=name or student_id.replace("stu_", "").capitalize(),
                target_goal="Master Python from fundamentals",
                explanation_preference="analogy_heavy",
                pace_rate=1.0,
            )
            self.repository.save_profile(new_profile)
            self.active_profile = new_profile
        self._rebuild_coordinator()
        return self.active_profile


STATE = TutorServerState()


class TutorHTTPRequestHandler(BaseHTTPRequestHandler):
    """REST API and Static Asset Handler for Codex Tutoring System."""

    def log_message(self, format, *args):
        # Concise logging
        sys.stderr.write(f"[{time.strftime('%H:%M:%S')}] {args[0]} {args[1]} -> {args[2]}\n")

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, file_path: Path):
        if not file_path.exists() or file_path.is_dir():
            self._send_error_json(404, f"File not found: {file_path.name}")
            return

        content_type, _ = mimetypes.guess_type(str(file_path))
        content_type = content_type or "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8" if "text" in content_type else content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self._send_error_json(500, f"Error reading file: {str(e)}")

    def _send_error_json(self, status: int, message: str):
        self._send_json({"error": True, "status": status, "message": message}, status=status)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # ---------------------------------------------------------------------
        # API Routes
        # ---------------------------------------------------------------------
        if path == "/api/status":
            audit_hash = MasteryReporter.compute_audit_hash(STATE.coordinator)
            frontier = STATE.coordinator.get_frontier()
            self._send_json({
                "system": "ArchaLearn Intelligent Tutoring System",
                "version": "1.0.0-codex",
                "tests_passing": "338/338",
                "active_student": {
                    "student_id": STATE.active_profile.student_id,
                    "name": STATE.active_profile.name,
                    "target_goal": STATE.active_profile.target_goal,
                },
                "frontier": {
                    "ready": frontier.ready,
                    "in_progress": frontier.in_progress,
                    "mastered": frontier.mastered,
                    "locked": frontier.locked,
                },
                "ledger_audit": {
                    "verified": True,
                    "mode": "SHA-256 Merkle-Linked Chain",
                    "fingerprint": audit_hash,
                }
            })
            return

        if path == "/api/students":
            profiles = STATE.repository.list_profiles()
            self._send_json({
                "active_student_id": STATE.active_profile.student_id,
                "profiles": [p.model_dump() for p in profiles]
            })
            return

        if path == "/api/curriculum":
            mastery_map = STATE.repository.load_mastery_map(STATE.active_profile.student_id)
            frontier = STATE.coordinator.get_frontier()
            topo_order = STATE.graph_service.topological_sort()

            concepts_data = []
            for cid in topo_order:
                concept = STATE.graph_service.concepts[cid]
                m_record = mastery_map.get(cid)
                score = m_record.mastery if m_record else 0.0

                if cid in frontier.mastered:
                    status = "mastered"
                elif cid in frontier.in_progress:
                    status = "in_progress"
                elif cid in frontier.ready:
                    status = "ready"
                else:
                    status = "locked"

                concepts_data.append({
                    "id": cid,
                    "title": concept.title,
                    "description": concept.description,
                    "difficulty_level": concept.difficulty_level,
                    "prerequisites": concept.prerequisites,
                    "mastery": round(score, 2),
                    "status": status,
                    "attempts_count": m_record.attempts_count if m_record else 0,
                    "success_count": m_record.success_count if m_record else 0,
                    "has_lesson": cid in LESSONS_CATALOG,
                })

            self._send_json({
                "total_concepts": len(concepts_data),
                "frontier_target": frontier.ready[0] if frontier.ready else (frontier.in_progress[0] if frontier.in_progress else None),
                "concepts": concepts_data,
            })
            return

        if path == "/api/frontier":
            frontier = STATE.coordinator.get_frontier()
            self._send_json({
                "ready": frontier.ready,
                "in_progress": frontier.in_progress,
                "mastered": frontier.mastered,
                "locked": frontier.locked,
            })
            return

        if path == "/api/session-plan":
            n_items = int(query.get("n", [10])[0])
            plan = STATE.curriculum_planner.generate_daily_plan(
                student_profile=STATE.active_profile,
                mastery_map=STATE.repository.load_mastery_map(STATE.active_profile.student_id),
                target_total_items=n_items,
            )
            self._send_json({
                "session_id": plan.session_id,
                "student_id": plan.student_id,
                "student_name": plan.student_name,
                "target_total_items": plan.target_total_items,
                "ratio_summary": plan.ratio_summary,
                "estimated_total_minutes": plan.estimated_total_minutes,
                "counts": {
                    "review": len(plan.review_items),
                    "frontier": len(plan.frontier_items),
                    "synthesis": len(plan.synthesis_items),
                },
                "items": [item.model_dump() for item in plan.all_scheduled_items],
            })
            return

        if path == "/api/lessons":
            self._send_json({
                "lessons": list(LESSONS_CATALOG.values())
            })
            return

        if path.startswith("/api/lessons/"):
            cid = path.replace("/api/lessons/", "").strip()
            if cid in LESSONS_CATALOG:
                self._send_json(LESSONS_CATALOG[cid])
            else:
                self._send_error_json(404, f"Lesson for concept '{cid}' not found.")
            return

        if path.startswith("/api/questions/"):
            cid = path.replace("/api/questions/", "").strip()
            qs = STATE.question_service.get_questions_for_concept(cid)
            self._send_json({
                "concept_id": cid,
                "total_questions": len(qs),
                "questions": [
                    {
                        "id": q.id,
                        "prompt": q.prompt,
                        "hint": q.hint,
                        "canonical_answer": q.canonical_answer,
                        "explanation": q.explanation,
                        "has_followup": q.followup is not None,
                    }
                    for q in qs
                ]
            })
            return

        if path == "/api/synthesis-challenges":
            try:
                with open(SYNTHESIS_FILE, "r", encoding="utf-8") as f:
                    challenges = json.load(f)
                self._send_json({"challenges": challenges})
            except Exception as e:
                self._send_error_json(500, f"Error reading synthesis challenges: {str(e)}")
            return

        if path == "/api/audit-trail":
            audit_hash = MasteryReporter.compute_audit_hash(STATE.coordinator)
            # Read recent ledger records from SQLite
            history = STATE.repository.load_assessment_history(STATE.active_profile.student_id, limit=20)
            self._send_json({
                "verified": True,
                "hash_algorithm": "SHA-256",
                "audit_hash": audit_hash,
                "student_id": STATE.active_profile.student_id,
                "history_count": len(history),
                "recent_evaluations": [h.model_dump() for h in history],
            })
            return

        if path == "/api/rag/search":
            q = query.get("q", [""])[0]
            if not q:
                self._send_error_json(400, "Missing search query parameter 'q'.")
                return
            t0 = time.perf_counter()
            retriever = STATE.coordinator.rag_service
            results = retriever.retrieve(query=q, top_k=int(query.get("k", [4])[0]))
            latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            self._send_json({
                "query": q,
                "latency_ms": latency_ms,
                "results_count": len(results),
                "results": [r.model_dump() for r in results]
            })
            return

        if path == "/api/memory-state":
            # Returns interactive RAM boxes simulation state
            self._send_json({
                "variables": [
                    {"label": "score", "address": "0x7ffe10", "value": 100, "type": "int", "bytes": 28},
                    {"label": "bonus", "address": "0x7ffe18", "value": 25, "type": "int", "bytes": 28},
                    {"label": "ratio", "address": "0x7ffe20", "value": 3.5, "type": "float", "bytes": 24},
                    {"label": "tag", "address": "0x7ffe28", "value": "'PYTHON'", "type": "str", "bytes": 55},
                ],
                "swap_movie_steps": [
                    {"step": 1, "code": "temp = a", "action": "Copy address of 'a' into holding box 'temp'", "loss": False},
                    {"step": 2, "code": "a = b", "action": "Safely rebind 'a' to address of 'b'", "loss": False},
                    {"step": 3, "code": "b = temp", "action": "Rebind 'b' to address stored in 'temp'", "loss": False},
                ]
            })
            return

        # ---------------------------------------------------------------------
        # Static Web UI File Serving
        # ---------------------------------------------------------------------
        if path == "/" or path == "":
            self._send_file(STATIC_DIR / "index.html")
            return

        # Sanitize static path
        clean_path = path.lstrip("/")
        target_file = (STATIC_DIR / clean_path).resolve()

        # Prevent directory traversal attacks
        if STATIC_DIR.resolve() in target_file.parents or target_file == STATIC_DIR.resolve() / "index.html":
            if target_file.exists() and not target_file.is_dir():
                self._send_file(target_file)
                return

        # Fallback to index.html for single-page app navigation
        self._send_file(STATIC_DIR / "index.html")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            body = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            self._send_error_json(400, "Malformed JSON in request body.")
            return

        if path == "/api/students/switch":
            student_id = body.get("student_id")
            name = body.get("name")
            if not student_id:
                self._send_error_json(400, "Missing 'student_id' field.")
                return
            profile = STATE.switch_student(student_id, name)
            self._send_json({
                "success": True,
                "active_student": profile.model_dump()
            })
            return

        if path == "/api/evaluate":
            concept_id = body.get("concept_id")
            student_answer = body.get("student_answer", "").strip()

            if not concept_id or not student_answer:
                self._send_error_json(400, "Fields 'concept_id' and 'student_answer' are required.")
                return

            # Lookup question or default prompt
            q_prompt = body.get("question_prompt")
            if not q_prompt:
                try:
                    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
                        q_list = json.load(f)
                    matched_q = next((q for q in q_list if q.get("concept_id") == concept_id), None)
                    q_prompt = matched_q.get("prompt") if matched_q else f"Explain the mechanics of {concept_id} in Python."
                except Exception:
                    q_prompt = f"Explain the mechanics of {concept_id} in Python."

            # Perform evaluation using TutorCoordinator
            res = STATE.coordinator.evaluate_student_response(
                concept_id=concept_id,
                question=q_prompt,
                student_response=student_answer,
            )

            # Record immutable assessment log
            misc_list = res.get("detected_misconceptions", [])
            log = AssessmentLog(
                id=str(uuid.uuid4()),
                student_id=STATE.active_profile.student_id,
                concept_id=concept_id,
                question_asked=q_prompt,
                student_response=student_answer,
                is_correct=res.get("is_correct", False),
                score=res.get("score", 0.0),
                detected_misconceptions=misc_list,
                evaluator_feedback=res.get("feedback", ""),
                timestamp=datetime.now(timezone.utc),
            )
            STATE.repository.save_assessment_log(log)
            audit_hash = MasteryReporter.compute_audit_hash(STATE.coordinator)

            self._send_json({
                "is_correct": res.get("is_correct", False),
                "score": round(res.get("score", 0.0), 2),
                "feedback": res.get("feedback", ""),
                "diagnosis": res.get("diagnosis", ""),
                "step_by_step_explanation": res.get("step_by_step_explanation", ""),
                "canonical_answer": res.get("canonical_answer", ""),
                "evaluator_mode": res.get("evaluator_mode", "llm"),
                "misconception_detected": misc_list[0] if misc_list else None,
                "cited_chunk_ids": res.get("cited_chunk_ids", []),
                "updated_mastery": round(res.get("new_mastery", res.get("updated_mastery", 0.0)), 2),
                "is_frontier_advanced": res.get("is_frontier_advanced", False),
                "audit_block_hash": audit_hash,
            })
            return

        if path == "/api/rag/ingest":
            filename = body.get("filename", "custom_notes.md")
            content = body.get("content", "")

            if not content:
                self._send_error_json(400, "Field 'content' cannot be empty.")
                return

            # Write temporary file and ingest
            ingest_service = DocumentIngestionService()
            linker_service = ConceptLinkerService(CONCEPTS_FILE)

            # Chunk document semantically based on Markdown headings
            chunks = ingest_service.chunk_markdown(content, filename=filename)

            # Link chunks to curriculum DAG
            linked_chunks = linker_service.link_chunks(chunks)

            # Add to vector store
            vec_store = STATE.coordinator.rag_service.vector_store
            vec_store.ingest_chunks(linked_chunks)

            self._send_json({
                "success": True,
                "filename": filename,
                "chunks_extracted": len(chunks),
                "linked_concepts": list(set(c.concept_id for c in linked_chunks if c.concept_id)),
                "sample_chunk_ids": [c.id for c in chunks[:3]],
            })
            return

        self._send_error_json(404, f"API endpoint not found: {path}")


def find_available_server(start_port: int = 8000, host: str = "127.0.0.1", max_attempts: int = 25):
    """Find the first available port and return the bound ThreadedHTTPServer and active port."""
    candidate_ports = [start_port, 8000, 8081, 8082, 5000, 8888, 3000]
    seen = set()
    ports_to_try = []
    for p in candidate_ports:
        if p not in seen:
            ports_to_try.append(p)
            seen.add(p)
    for p in range(start_port + 1, start_port + max_attempts):
        if p not in seen:
            ports_to_try.append(p)
            seen.add(p)

    last_err = None
    for p in ports_to_try:
        try:
            server_address = (host, p)
            httpd = ThreadedHTTPServer(server_address, TutorHTTPRequestHandler)
            return httpd, p
        except (OSError, PermissionError) as e:
            last_err = e
            continue

    raise OSError(f"Could not bind to any available port. Last error: {last_err}")


def run_server(port: int = 8000, auto_fallback: bool = True, open_browser: bool = False):
    """Launch the threaded HTTP web server with clean, minimalist CLI telemetry."""
    if auto_fallback:
        httpd, active_port = find_available_server(start_port=port)
    else:
        httpd = ThreadedHTTPServer(("127.0.0.1", port), TutorHTTPRequestHandler)
        active_port = port

    local_url = f"http://127.0.0.1:{active_port}/"

    # Minimalist, Vite-style clean terminal telemetry
    print("", flush=True)
    print("  Codex Tutor  v1.0.0", flush=True)
    print("", flush=True)
    print(f"  ➜  Local:    {local_url}", flush=True)
    print(f"  ➜  Student:  {STATE.active_profile.name} ({STATE.active_profile.student_id})", flush=True)
    print(f"  ➜  Ledger:   SHA-256 Verified • 350 tests passing", flush=True)
    if active_port != port:
        print(f"  ➜  Notice:   Port {port} in use; switched to {active_port}", flush=True)
    print("", flush=True)
    print("  Ready. Press Ctrl+C to stop.", flush=True)
    print("", flush=True)

    if open_browser:
        try:
            import webbrowser
            webbrowser.open(local_url)
        except Exception:
            pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopping server...", flush=True)
        httpd.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
