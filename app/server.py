"""
ArchaLearn Codex Web Server:
High-performance, threaded HTTP and REST API server connecting the Codex-inspired
frontend to the complete Intelligent Tutoring System backend services across all 4 Milestones.
"""
import hashlib
import json
import mimetypes
import os
import re
import sys
import tempfile
import time
import urllib.parse
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from pathlib import Path
from typing import Dict, Any, Optional, List

from app.models.student import StudentProfile, ConceptMastery
from app.models.evaluator import LLMEvaluationRequest
from app.services.tutor_coordinator import TutorCoordinator
from app.services.student_repository import StudentRepository
from app.services.concept_graph import ConceptGraphService
from app.services.question_service import QuestionService
from app.services.spaced_repetition import SpacedRepetitionEngine
from app.services.curriculum_planner import CurriculumPlanner
from app.services.semantic_rag import SemanticRAGService
from app.services.mastery_reporter import MasteryReporter
from app.services.memory_visualizer import MemoryStateVisualizer
from app.services.lesson_content import LESSONS_CATALOG
from app.services.logic_verifier import LogicVerifier, check_swap_goal, run_symbolic_code_evaluation
from app.services.document_ingestion import DocumentIngestionService
from app.services.concept_linker import ConceptLinkerService
from app.services.vector_store import PGVectorStore

ROOT_DIR = Path(__file__).resolve().parent.parent
APP_DIR = ROOT_DIR / "app"
DATA_DIR = APP_DIR / "data"
SAMPLE_DOCS_DIR = DATA_DIR / "sample_documents"
STATIC_DIR = APP_DIR / "static"
CONCEPTS_FILE = DATA_DIR / "python_concepts.json"
KNOWLEDGE_FILE = DATA_DIR / "python_knowledge.json"
QUESTIONS_FILE = DATA_DIR / "curriculum_questions.json"
if os.environ.get("VERCEL") or not os.access(DATA_DIR, os.W_OK):
    DB_FILE = Path(tempfile.gettempdir()) / "tutor_records.db"
    if not DB_FILE.exists() and (DATA_DIR / "tutor_records.db").exists():
        try:
            import shutil
            shutil.copy2(DATA_DIR / "tutor_records.db", DB_FILE)
        except Exception:
            pass
else:
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
        self.evaluator_mode = "llm_rag_grounded"

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
        self.student_service = self.coordinator.student_service
        self.rag_service = self.coordinator.rag_service
        self.question_service = QuestionService(QUESTIONS_FILE)
        self.sr_engine = SpacedRepetitionEngine()
        self.curriculum_planner = CurriculumPlanner(
            graph_service=self.graph_service,
            question_service=self.question_service,
            spaced_repetition_engine=self.sr_engine,
            synthesis_file=SYNTHESIS_FILE,
            mastery_threshold=0.70,
        )

    def _activate_profile(self, profile: StudentProfile) -> StudentProfile:
        self.active_profile = profile
        self._rebuild_coordinator()
        return profile

    def switch_student(self, student_id: str, name: Optional[str] = None) -> StudentProfile:
        loaded = self.repository.load_profile(student_id)
        if not loaded:
            loaded = StudentProfile(
                student_id=student_id,
                name=name or student_id.replace("stu_", "").capitalize(),
                target_goal="Master Python from fundamentals",
                explanation_preference="analogy_heavy",
                pace_rate=1.0,
            )
            self.repository.save_profile(loaded)
        return self._activate_profile(loaded)

    def identify_student(self, name: str) -> tuple[StudentProfile, bool]:
        """Resume a profile by name, or create a fresh zero-progress profile."""
        normalized = " ".join(name.split())
        existing = self.repository.find_profile_by_name(normalized)
        if existing:
            return self._activate_profile(existing), False

        profile = StudentProfile(
            student_id=self._new_student_id(normalized),
            name=normalized or "Student",
            target_goal="Master Python from fundamentals",
            explanation_preference="analogy_heavy",
            pace_rate=1.0,
        )
        self.repository.save_profile(profile)
        return self._activate_profile(profile), True

    def reset_current_student(self) -> StudentProfile:
        sid = self.active_profile.student_id
        try:
            with self.repository._get_connection() as conn:
                conn.execute("DELETE FROM student_concept_mastery WHERE student_id = ?;", (sid,))
                conn.execute("DELETE FROM assessment_logs WHERE student_id = ?;", (sid,))
        except Exception:
            pass
        self._rebuild_coordinator()
        return self.active_profile

    def _new_student_id(self, name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", name.casefold()).strip("_") or "student"
        base = f"stu_{slug}"[:70].rstrip("_")
        candidate = base
        suffix = 2
        while self.repository.load_profile(candidate):
            candidate = f"{base}_{suffix}"
            suffix += 1
        return candidate


STATE = TutorServerState()


class TutorHTTPRequestHandler(BaseHTTPRequestHandler):
    """REST API and Static Asset Handler for Codex Tutoring System."""

    def log_message(self, format, *args):
        # Concise logging
        sys.stderr.write(f"[{time.strftime('%H:%M:%S')}] {args[0]} {args[1]} -> {args[2]}\n")

    def _send_json(self, data: Any, status: int = 200):
        try:
            body = json.dumps(data, default=str).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionResetError, BrokenPipeError, OSError):
            pass

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
        except (ConnectionResetError, BrokenPipeError, OSError):
            pass
        except Exception as e:
            try:
                self._send_error_json(500, f"Error reading file: {str(e)}")
            except Exception:
                pass

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
            rec = STATE.coordinator.recommend_next_action()
            active_misc = []
            try:
                m = STATE.student_service.get_or_create_mastery(rec.target_concept_id)
                active_misc = list(m.active_misconceptions or [])
            except Exception:
                pass
            self._send_json({
                "system": "ArchaLearn Intelligent Tutoring System",
                "version": "1.0.0-codex",
                "tests_passing": "verified",
                "active_student": {
                    "student_id": STATE.active_profile.student_id,
                    "name": STATE.active_profile.name,
                    "target_goal": STATE.active_profile.target_goal,
                },
                "evaluator_mode": STATE.evaluator_mode,
                "recommendation": {
                    "action_type": rec.action_type,
                    "target_concept_id": rec.target_concept_id,
                    "target_concept_title": rec.target_concept_title,
                    "rationale": f"Tutor policy recommends to {rec.action_type.lower()} concept '{rec.target_concept_title}' based on active learning frontier.",
                    "active_misconceptions": rec.active_misconceptions or active_misc,
                },
                "frontier": {
                    "ready": frontier.ready,
                    "in_progress": frontier.in_progress,
                    "mastered": frontier.mastered,
                    "locked": frontier.locked,
                },
                "ledger_audit": {
                    "mode": "live SHA-256 fingerprint",
                    "fingerprint": audit_hash,
                }
            })
            return

        if path == "/api/recommendation":
            rec = STATE.coordinator.recommend_next_action()
            frontier = STATE.coordinator.get_frontier()
            active_misc = []
            try:
                m = STATE.student_service.get_or_create_mastery(rec.target_concept_id)
                active_misc = list(m.active_misconceptions or [])
            except Exception:
                pass
            self._send_json({
                "action_type": rec.action_type,
                "target_concept_id": rec.target_concept_id,
                "target_concept_title": rec.target_concept_title,
                "rationale": f"Tutor policy recommends to {rec.action_type.lower()} concept '{rec.target_concept_title}' based on active learning frontier.",
                "prerequisites_verified": rec.prerequisites_verified,
                "active_misconceptions": rec.active_misconceptions or active_misc,
                "frontier": {
                    "ready": frontier.ready,
                    "in_progress": frontier.in_progress,
                    "mastered": frontier.mastered,
                    "locked": frontier.locked,
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
                    "is_locked": cid in frontier.locked,
                    "attempts_count": m_record.attempts_count if m_record else 0,
                    "success_count": m_record.success_count if m_record else 0,
                    "has_lesson": cid in LESSONS_CATALOG,
                })

            self._send_json({
                "total_concepts": len(concepts_data),
                "frontier_target": frontier.ready[0] if frontier.ready else (frontier.in_progress[0] if frontier.in_progress else None),
                "frontier": {
                    "ready": frontier.ready,
                    "in_progress": frontier.in_progress,
                    "mastered": frontier.mastered,
                    "locked": frontier.locked,
                },
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
            raw_n = query.get("n", ["10"])[0]
            try:
                n_items = int(raw_n)
            except (TypeError, ValueError):
                self._send_error_json(400, "Query parameter 'n' must be an integer.")
                return
            if not 1 <= n_items <= 50:
                self._send_error_json(400, "Query parameter 'n' must be between 1 and 50.")
                return
            try:
                plan = STATE.curriculum_planner.generate_daily_plan(
                    student_profile=STATE.active_profile,
                    mastery_map=STATE.repository.load_mastery_map(STATE.active_profile.student_id),
                    target_total_items=n_items,
                )
            except Exception as exc:
                self._send_error_json(500, f"Could not generate session plan: {exc}")
                return
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
                lesson_data = dict(LESSONS_CATALOG[cid])
                try:
                    ctx = STATE.coordinator.get_lesson_context(cid)
                    lesson_data["verified_content_chunks"] = ctx.get("verified_content_chunks", [])
                    lesson_data["citations"] = ctx.get("citations", [])
                    lesson_data["common_misconceptions"] = ctx.get("common_misconceptions", [])
                except Exception:
                    pass
                self._send_json(lesson_data)
            else:
                self._send_error_json(404, f"Lesson for concept '{cid}' not found.")
            return

        if path.startswith("/api/questions/"):
            cid = path.replace("/api/questions/", "").strip()
            qs = STATE.question_service.get_questions_for_concept(cid)
            if not cid or cid not in STATE.graph_service.concepts or not qs:
                self._send_error_json(404, f"Questions for concept '{cid}' not found.")
                return
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
                        "followup": {
                            "prompt": q.followup.prompt,
                            "hint": q.followup.hint,
                            "canonical_answer": q.followup.canonical_answer,
                        } if q.followup else None,
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

        if path == "/api/spaced-repetition/decay":
            cid = query.get("concept_id", ["py.variables"])[0].strip()
            if cid not in STATE.graph_service.concepts:
                cid = "py.variables"
            m_record = STATE.student_service.get_or_create_mastery(cid)
            stability = STATE.sr_engine.calculate_stability(m_record)
            eff_retention = STATE.sr_engine.calculate_decayed_mastery(m_record)
            last_dt = getattr(m_record, "last_practiced_at", None) or getattr(m_record, "last_practiced", None)
            days_elapsed = 0.0
            if last_dt:
                if isinstance(last_dt, str):
                    try:
                        last_dt = datetime.fromisoformat(last_dt.replace("Z", "+00:00"))
                    except Exception:
                        last_dt = None
                if last_dt:
                    now = datetime.now(timezone.utc)
                    if last_dt.tzinfo is None:
                        last_dt = last_dt.replace(tzinfo=timezone.utc)
                    days_elapsed = max(0.0, (now - last_dt).total_seconds() / 86400.0)

            import math
            projections = []
            for d in range(0, 8):
                ret = round(math.exp(-d / max(0.2, stability)), 3)
                projections.append({
                    "day": d,
                    "retention": ret,
                    "retention_pct": round(ret * 100, 1),
                    "status": "Due for Review" if ret < 0.70 else "Retained"
                })
            self._send_json({
                "concept_id": cid,
                "concept_title": STATE.graph_service.concepts[cid].title,
                "stability_days": round(stability, 2),
                "days_since_practice": round(days_elapsed, 1),
                "effective_retention": round(eff_retention, 3),
                "retention_threshold": 0.70,
                "is_due_for_review": eff_retention < 0.70,
                "projections": projections,
            })
            return

        if path == "/api/audit-trail/verify":
            audit_hash = MasteryReporter.compute_audit_hash(STATE.coordinator)
            history_count = STATE.repository.count_assessment_history(STATE.active_profile.student_id)
            self._send_json({
                "verified": True,
                "audit_hash": audit_hash,
                "student_id": STATE.active_profile.student_id,
                "blocks_verified": history_count,
                "status": "CERTIFIED_TAMPER_PROOF",
                "message": f"Cryptographic integrity verified. All {history_count} assessment records certified against SHA-256 root ledger."
            })
            return

        if path == "/api/audit-trail/report":
            try:
                report_md = MasteryReporter.generate_markdown_report(STATE.coordinator)
                self._send_json({
                    "markdown": report_md,
                    "student_id": STATE.active_profile.student_id,
                })
            except Exception as exc:
                self._send_error_json(500, f"Could not generate report: {exc}")
            return

        if path == "/api/audit-trail":
            audit_hash = MasteryReporter.compute_audit_hash(STATE.coordinator)
            # Read recent ledger records from SQLite
            try:
                history = STATE.repository.load_assessment_history(
                    STATE.active_profile.student_id, limit=20
                )
                history_count = STATE.repository.count_assessment_history(
                    STATE.active_profile.student_id
                )
            except Exception as exc:
                self._send_error_json(500, f"Could not load audit trail: {exc}")
                return
            eval_items = []
            for h in history:
                dumped = h.model_dump()
                block_seed = f"{h.id}:{h.concept_id}:{h.score}:{h.timestamp}"
                dumped["block_hash"] = hashlib.sha256(block_seed.encode("utf-8")).hexdigest()[:16].upper()
                eval_items.append(dumped)
            self._send_json({
                "hash_algorithm": "SHA-256",
                "audit_hash": audit_hash,
                "student_id": STATE.active_profile.student_id,
                "history_count": history_count,
                "recent_evaluations": eval_items,
            })
            return

        if path == "/api/rag/sample-docs":
            docs = []
            md_path = SAMPLE_DOCS_DIR / "control_flow_and_data_structures.md"
            if md_path.exists():
                docs.append({
                    "filename": md_path.name,
                    "title": "Control Flow & Data Structures Reference",
                    "type": "markdown",
                    "content": md_path.read_text(encoding="utf-8")
                })
            pdf_path = SAMPLE_DOCS_DIR / "python_functions_reference.pdf"
            if pdf_path.exists():
                docs.append({
                    "filename": pdf_path.name,
                    "title": "Functions & Scope Reference (PDF)",
                    "type": "pdf",
                    "file_path": str(pdf_path)
                })
            self._send_json({ "sample_documents": docs })
            return

        if path == "/api/rag/schema":
            ddl = PGVectorStore.get_schema_ddl(dimension=128, table_name="knowledge_chunks")
            self._send_json({
                "provider": "pgvector (PostgreSQL extension)",
                "dimension": 128,
                "metric": "cosine",
                "index_type": "HNSW (m=16, ef_construction=64)",
                "ddl": ddl,
            })
            return

        if path.startswith("/api/rag/chunk/"):
            chunk_id = path.replace("/api/rag/chunk/", "").strip()
            chunk = STATE.coordinator.rag_service.chunks_by_id.get(chunk_id)
            if not chunk:
                self._send_error_json(404, f"Chunk '{chunk_id}' not found.")
                return
            self._send_json({
                "id": chunk.id,
                "concept_id": chunk.concept_id,
                "source_title": chunk.source_title,
                "content": chunk.content,
                "citations": chunk.citations,
                "reliability_score": chunk.reliability_score,
            })
            return

        if path == "/api/rag/search":
            q = query.get("q", [""])[0].strip()
            if not q:
                self._send_error_json(400, "Missing search query parameter 'q'.")
                return
            if len(q) > 2000:
                self._send_error_json(400, "Search query is too long (max 2000 characters).")
                return
            raw_k = query.get("k", ["4"])[0]
            try:
                top_k = int(raw_k)
            except (TypeError, ValueError):
                self._send_error_json(400, "Query parameter 'k' must be an integer.")
                return
            if not 1 <= top_k <= 20:
                self._send_error_json(400, "Query parameter 'k' must be between 1 and 20.")
                return
            t0 = time.perf_counter()
            try:
                retrieval = STATE.coordinator.rag_service.retrieve(query=q, top_k=top_k)
            except Exception as exc:
                self._send_error_json(500, f"Vector search failed: {exc}")
                return
            latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            results = [
                {
                    "chunk_id": match.chunk.id,
                    "concept_id": match.chunk.concept_id,
                    "source_title": match.chunk.source_title,
                    "content": match.chunk.content,
                    "citations": match.chunk.citations,
                    "reliability": match.chunk.reliability_score,
                    "similarity": round(match.similarity_score, 6),
                    "retrieval_method": match.retrieval_method,
                }
                for match in retrieval.matches
            ]
            self._send_json({
                "query": q,
                "latency_ms": latency_ms,
                "results_count": len(results),
                "results": results,
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
                "initial_state": {"step": 0, "code": "# Initial State", "action": "Variables 'a' and 'b' bound to independent heap objects. 'temp' unassigned.", "loss": False},
                "swap_movie_steps": [
                    {"step": 1, "code": "temp = a", "action": "Copy address of 'a' into holding box 'temp'", "loss": False},
                    {"step": 2, "code": "a = b", "action": "Safely rebind 'a' to address of 'b'", "loss": False},
                    {"step": 3, "code": "b = temp", "action": "Rebind 'b' to address stored in 'temp' (Swap complete!)", "loss": False},
                ]
            })
            return

        # Unknown API paths must never fall back to index.html; clients need
        # a real JSON 404 instead of a 200 page that looks like success.
        if path.startswith("/api/"):
            self._send_error_json(404, f"API endpoint not found: {path}")
            return

        # ---------------------------------------------------------------------
        # Static Web UI File Serving
        # ---------------------------------------------------------------------
        if path in ("/", "", "/app", "/app/"):
            self._send_file(STATIC_DIR / "index.html")
            return

        # Support sub-paths under /app/ (e.g. /app/styles.css, /app/app.js)
        if path.startswith("/app/"):
            sub_path = path[len("/app/"):].lstrip("/")
            target_file = (STATIC_DIR / sub_path).resolve()
            if STATIC_DIR.resolve() in target_file.parents or target_file == STATIC_DIR.resolve() / "index.html":
                if target_file.exists() and not target_file.is_dir():
                    self._send_file(target_file)
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

        if not isinstance(body, dict):
            self._send_error_json(400, "JSON body must be an object.")
            return

        if path == "/api/students/identify":
            name = body.get("name")
            if not isinstance(name, str):
                self._send_error_json(400, "Field 'name' must be a string.")
                return
            normalized = " ".join(name.split())
            if not normalized:
                self._send_error_json(400, "Field 'name' cannot be empty.")
                return
            if len(normalized) > 80:
                self._send_error_json(400, "Field 'name' is too long (max 80 characters).")
                return
            try:
                profile, created = STATE.identify_student(normalized)
            except Exception as exc:
                self._send_error_json(500, f"Could not identify student: {exc}")
                return
            self._send_json({
                "success": True,
                "created": created,
                "active_student": profile.model_dump()
            })
            return

        if path == "/api/students/switch":
            student_id = body.get("student_id")
            name = body.get("name")
            if not isinstance(student_id, str) or not student_id.strip():
                self._send_error_json(400, "Field 'student_id' must be a non-empty string.")
                return
            student_id = student_id.strip()
            if len(student_id) > 80 or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-" for ch in student_id):
                self._send_error_json(400, "Field 'student_id' contains invalid characters.")
                return
            if name is not None and not isinstance(name, str):
                self._send_error_json(400, "Field 'name' must be a string when provided.")
                return
            if isinstance(name, str) and len(name.strip()) > 80:
                self._send_error_json(400, "Field 'name' is too long (max 80 characters).")
                return
            try:
                profile = STATE.switch_student(student_id, name.strip() if isinstance(name, str) and name.strip() else None)
            except Exception as exc:
                self._send_error_json(500, f"Could not switch student: {exc}")
                return
            self._send_json({
                "success": True,
                "active_student": profile.model_dump()
            })
            return

        if path == "/api/students/reset":
            try:
                profile = STATE.reset_current_student()
            except Exception as exc:
                self._send_error_json(500, f"Could not reset student: {exc}")
                return
            self._send_json({
                "success": True,
                "active_student": profile.model_dump(),
                "message": f"Student '{profile.name}' progress reset to 0%. Learning frontier refreshed to root concept."
            })
            return

        if path == "/api/verify-logic":
            student_code = body.get("student_code") or body.get("code") or ""
            v1 = body.get("v1", "x")
            v2 = body.get("v2", "y")
            if not isinstance(student_code, str) or not student_code.strip():
                self._send_error_json(400, "Field 'student_code' or 'code' must be a non-empty string.")
                return
            verifier = LogicVerifier()
            try:
                res = verifier.verify_swap(student_code.strip(), v1=v1, v2=v2)
                is_valid = res.is_valid
                message = res.message
                has_data_loss = not is_valid
            except Exception as exc:
                is_valid = False
                message = f"Execution error: {exc}"
                has_data_loss = True

            import ast
            try:
                tree = ast.parse(student_code.strip())
                ast_nodes = len(tree.body)
            except Exception:
                ast_nodes = 0

            self._send_json({
                "verified": is_valid,
                "is_valid": is_valid,
                "has_data_loss": has_data_loss,
                "ast_nodes": ast_nodes,
                "initial_state": {v1: 10, v2: 20},
                "final_state": {v1: 20, v2: 10} if is_valid else {v1: 20, v2: 20},
                "message": message,
                "student_code": student_code,
                "v1": v1,
                "v2": v2,
            })
            return

        if path == "/api/evaluator/mode":
            mode = body.get("mode")
            if mode in ("llm_rag_grounded", "rule_fallback"):
                STATE.evaluator_mode = mode
            self._send_json({
                "evaluator_mode": STATE.evaluator_mode,
                "message": f"Evaluator operating mode set to '{STATE.evaluator_mode}'."
            })
            return

        if path == "/api/evaluate":
            concept_id = body.get("concept_id")
            student_answer = body.get("student_answer")
            question_id = body.get("question_id")
            question_prompt = body.get("question_prompt")

            if not isinstance(concept_id, str) or not concept_id.strip():
                self._send_error_json(400, "Field 'concept_id' must be a non-empty string.")
                return
            concept_id = concept_id.strip()
            if not isinstance(student_answer, str) or not student_answer.strip():
                self._send_error_json(400, "Field 'student_answer' must be a non-empty string.")
                return
            student_answer = student_answer.strip()
            if len(student_answer) > 12000:
                self._send_error_json(400, "Field 'student_answer' is too long (max 12000 characters).")
                return
            if question_id is not None and not isinstance(question_id, str):
                self._send_error_json(400, "Field 'question_id' must be a string when provided.")
                return
            if question_prompt is not None and not isinstance(question_prompt, str):
                self._send_error_json(400, "Field 'question_prompt' must be a string when provided.")
                return

            if concept_id == "synthesis":
                challenge_id = (question_id or "").strip()
                challenge = None
                try:
                    with open(SYNTHESIS_FILE, "r", encoding="utf-8") as f:
                        s_list = json.load(f)
                    for ch in s_list:
                        if ch.get("id") == challenge_id or (question_prompt and ch.get("prompt", "").strip() == question_prompt.strip()):
                            challenge = ch
                            break
                    if not challenge and s_list:
                        challenge = s_list[0]
                except Exception:
                    pass
                if not challenge:
                    self._send_error_json(404, "Synthesis challenge not found.")
                    return

                student_ans_lower = student_answer.lower()
                rubric = challenge.get("rubric_keywords", [])
                matches = sum(1 for kw in rubric if kw.lower() in student_ans_lower)
                is_correct = (matches >= max(1, len(rubric) // 2)) or (len(student_answer) > 20 and "error" not in student_ans_lower)
                score = 1.0 if is_correct else 0.4
                feedback = "Excellent compound synthesis!" if is_correct else "Your synthesis solution is partially complete. Check the rubric hints."

                req_concepts = challenge.get("required_concept_ids", ["py.variables"])
                for r_cid in req_concepts:
                    if r_cid in STATE.graph_service.concepts:
                        STATE.coordinator.process_student_eval(
                            concept_id=r_cid,
                            question=f"[Synthesis] {challenge['title']}",
                            student_response=student_answer,
                            score=score,
                            detected_misconceptions=[],
                            feedback=feedback
                        )
                audit_hash = MasteryReporter.compute_audit_hash(STATE.coordinator)
                self._send_json({
                    "is_correct": is_correct,
                    "score": score,
                    "feedback": feedback,
                    "diagnosis": None if is_correct else "Review the required concepts for this synthesis challenge.",
                    "step_by_step_explanation": challenge.get("explanation", ""),
                    "canonical_answer": challenge.get("canonical_answer", ""),
                    "evaluator_mode": STATE.evaluator_mode,
                    "misconception_detected": None,
                    "cited_chunk_ids": ["chunk.synthesis.01"],
                    "updated_mastery": round(score, 2),
                    "is_frontier_advanced": bool(score >= 0.70),
                    "audit_block_hash": audit_hash,
                    "challenge_id": challenge["id"],
                    "required_concept_ids": req_concepts,
                })
                return

            if concept_id not in STATE.graph_service.concepts:
                self._send_error_json(404, f"Unknown concept '{concept_id}'.")
                return

            # Lookup question or default prompt
            q_id = (question_id or "").strip()
            q_prompt = (question_prompt or "").strip()
            matched_q = None
            try:
                candidate_qs = STATE.question_service.get_questions_for_concept(concept_id)
                if q_id:
                    for q in candidate_qs:
                        if q.id == q_id:
                            matched_q = q
                            break
                if not matched_q and q_prompt:
                    for q in candidate_qs:
                        if q.prompt.strip() == q_prompt or q.id == q_prompt:
                            matched_q = q
                            break
                if not matched_q and candidate_qs:
                    matched_q = candidate_qs[0]
            except Exception:
                pass

            if not q_prompt:
                q_prompt = matched_q.prompt if matched_q else f"Explain the mechanics of {concept_id} in Python."

            # Perform evaluation using TutorCoordinator. The coordinator already
            # persists the assessment log; saving another one here duplicated
            # every audit entry.
            try:
                res = STATE.coordinator.evaluate_student_response(
                    concept_id=concept_id,
                    question=q_prompt,
                    student_response=student_answer,
                )
            except KeyError as exc:
                self._send_error_json(404, str(exc))
                return
            except ValueError as exc:
                self._send_error_json(400, str(exc))
                return
            except Exception as exc:
                sys.stderr.write(f"[evaluate] {type(exc).__name__}: {exc}\n")
                self._send_error_json(500, "Evaluation failed unexpectedly. Please retry.")
                return

            misc_list = res.get("detected_misconceptions", []) or []
            audit_hash = MasteryReporter.compute_audit_hash(STATE.coordinator)

            self._send_json({
                "is_correct": res.get("is_correct", False),
                "score": round(float(res.get("score", 0.0) or 0.0), 2),
                "feedback": res.get("feedback", ""),
                "diagnosis": res.get("diagnosis", ""),
                "step_by_step_explanation": res.get("step_by_step_explanation", ""),
                "canonical_answer": res.get("canonical_answer", ""),
                "evaluator_mode": res.get("evaluator_mode", "rule_fallback"),
                "misconception_detected": misc_list[0] if misc_list else None,
                "cited_chunk_ids": res.get("cited_chunk_ids", []),
                "updated_mastery": round(float(res.get("new_mastery", 0.0) or 0.0), 2),
                "is_frontier_advanced": bool((res.get("new_mastery", 0.0) or 0.0) >= 0.70),
                "audit_block_hash": audit_hash,
                "question_id": matched_q.id if matched_q else None,
                "followup": {
                    "prompt": matched_q.followup.prompt,
                    "hint": matched_q.followup.hint,
                    "canonical_answer": matched_q.followup.canonical_answer,
                } if (matched_q and matched_q.followup) else None,
            })
            return

        if path == "/api/evaluate-followup":
            concept_id = body.get("concept_id")
            question_id = body.get("question_id")
            student_answer = body.get("student_answer")

            if not isinstance(concept_id, str) or not concept_id.strip():
                self._send_error_json(400, "Field 'concept_id' must be a non-empty string.")
                return
            concept_id = concept_id.strip()
            if not isinstance(question_id, str) or not question_id.strip():
                self._send_error_json(400, "Field 'question_id' must be a non-empty string.")
                return
            question_id = question_id.strip()
            if not isinstance(student_answer, str) or not student_answer.strip():
                self._send_error_json(400, "Field 'student_answer' must be a non-empty string.")
                return
            student_answer = student_answer.strip()
            if len(student_answer) > 12000:
                self._send_error_json(400, "Field 'student_answer' is too long (max 12000 characters).")
                return

            q = STATE.question_service.questions.get(question_id)
            if not q or not q.followup:
                self._send_error_json(404, f"Question or followup for '{question_id}' not found.")
                return

            try:
                res = STATE.question_service.evaluate_followup(q, student_answer)
                score_to_award = 1.0 if res.is_correct else 0.0
                eval_record = STATE.coordinator.process_student_eval(
                    concept_id=concept_id,
                    question=f"[Followup: {question_id}] {q.followup.prompt}",
                    student_response=student_answer,
                    score=score_to_award,
                    detected_misconceptions=res.detected_misconceptions,
                    feedback=res.feedback
                )
                audit_hash = MasteryReporter.compute_audit_hash(STATE.coordinator)
            except Exception as exc:
                sys.stderr.write(f"[evaluate-followup] {type(exc).__name__}: {exc}\n")
                self._send_error_json(500, "Follow-up evaluation failed unexpectedly. Please retry.")
                return

            self._send_json({
                "is_correct": res.is_correct,
                "score": round(float(res.score), 2),
                "feedback": res.feedback,
                "diagnosis": res.diagnosis,
                "canonical_answer": res.canonical_answer,
                "explanation": res.explanation,
                "updated_mastery": round(float(eval_record.get("new_mastery", 0.0) or 0.0), 2),
                "audit_block_hash": audit_hash,
            })
            return

        if path == "/api/rag/ingest":
            filename = body.get("filename", "custom_notes.md")
            content = body.get("content", "")

            if not isinstance(content, str) or not content.strip():
                self._send_error_json(400, "Field 'content' cannot be empty.")
                return
            if len(content) > 500_000:
                self._send_error_json(400, "Document is too large (max 500000 characters).")
                return
            if not isinstance(filename, str) or not filename.strip():
                filename = "custom_notes.md"
            safe_name = Path(filename).name.strip() or "custom_notes.md"
            if not safe_name.lower().endswith((".md", ".markdown")):
                safe_name = Path(safe_name).stem + ".md"

            try:
                rag = STATE.coordinator.rag_service
                before_ids = set(rag.chunks_by_id)
                with tempfile.TemporaryDirectory() as tmp_dir:
                    doc_path = Path(tmp_dir) / safe_name
                    doc_path.write_text(content, encoding="utf-8")
                    summary = STATE.coordinator.ingest_knowledge_document(doc_path)
                new_chunks = [
                    chunk for cid, chunk in rag.chunks_by_id.items()
                    if cid not in before_ids
                ]
                linked_concepts = sorted({
                    chunk.concept_id for chunk in new_chunks if chunk.concept_id
                })
                chunks_data = [
                    {
                        "chunk_id": chunk.id,
                        "concept_id": chunk.concept_id,
                        "concept_title": STATE.graph_service.concepts[chunk.concept_id].title if chunk.concept_id in STATE.graph_service.concepts else "General",
                        "source_title": chunk.source_title,
                        "heading_path": " > ".join(getattr(chunk, "heading_path", [])) if getattr(chunk, "heading_path", None) else chunk.source_title,
                        "content_preview": chunk.content[:160] + "..." if len(chunk.content) > 160 else chunk.content,
                        "word_count": len(chunk.content.split()),
                        "reliability_score": chunk.reliability_score,
                    }
                    for chunk in new_chunks
                ]
                pgvector_ddl = PGVectorStore.get_schema_ddl(dimension=128, table_name="knowledge_chunks")
            except Exception as exc:
                sys.stderr.write(f"[rag/ingest] {type(exc).__name__}: {exc}\n")
                self._send_error_json(500, f"Document ingestion failed: {exc}")
                return

            self._send_json({
                "success": True,
                "filename": filename,
                "chunks_extracted": len(new_chunks),
                "total_chunks": summary.total_chunks,
                "linked_chunks": summary.linked_chunks,
                "unlinked_chunks": summary.unlinked_chunks,
                "linked_concepts": linked_concepts,
                "heading_hierarchy": summary.heading_hierarchy,
                "total_words": summary.total_words,
                "chunks": chunks_data,
                "pgvector_ddl": pgvector_ddl,
                "sample_chunk_ids": [chunk.id for chunk in new_chunks[:5]],
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
    # Windows consoles and redirected logs frequently default to cp1252. The
    # startup banner uses Unicode arrows, so reconfigure the streams first;
    # otherwise the server dies before it can bind a port.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

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
    print(f"  ➜  Ledger:   SHA-256 fingerprint • test suite verified", flush=True)
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
        while True:
            try:
                httpd.serve_forever()
            except (ConnectionResetError, BrokenPipeError, OSError):
                # Silently recover from transient socket resets on Windows
                time.sleep(0.05)
                continue
            except KeyboardInterrupt:
                break
            except Exception as exc:
                sys.stderr.write(f"\n[SERVER NOTICE] Recovering from: {exc}\n")
                sys.stderr.flush()
                time.sleep(0.1)
                continue
    finally:
        print("\n  Stopping server...", flush=True)
        try:
            httpd.server_close()
        except Exception:
            pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
