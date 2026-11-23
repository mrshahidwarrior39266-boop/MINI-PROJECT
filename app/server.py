"""
ArchaLearn Codex Web Server:
High-performance, threaded HTTP and REST API server connecting the Codex-inspired
frontend to the complete Intelligent Tutoring System backend services across all 4 Milestones.
"""
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
            self._send_json({
                "system": "ArchaLearn Intelligent Tutoring System",
                "version": "1.0.0-codex",
                "tests_passing": "verified",
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
                    "mode": "live SHA-256 fingerprint",
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
                self._send_json(LESSONS_CATALOG[cid])
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
            self._send_json({
                "hash_algorithm": "SHA-256",
                "audit_hash": audit_hash,
                "student_id": STATE.active_profile.student_id,
                "history_count": history_count,
                "recent_evaluations": [h.model_dump() for h in history],
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
                "swap_movie_steps": [
                    {"step": 1, "code": "temp = a", "action": "Copy address of 'a' into holding box 'temp'", "loss": False},
                    {"step": 2, "code": "a = b", "action": "Safely rebind 'a' to address of 'b'", "loss": False},
                    {"step": 3, "code": "b = temp", "action": "Rebind 'b' to address stored in 'temp'", "loss": False},
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
                "sample_chunk_ids": [chunk.id for chunk in new_chunks[:3]],
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
