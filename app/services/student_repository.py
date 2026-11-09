"""
Student Repository:
Persistent SQLite storage engine for Student Profiles, Concept Mastery,
Assessment Audit Logs, and Session Progress Cursors.
Guarantees ACID transactions, zero data loss, and seamless cross-session resumption.
"""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Generator

from app.models.student import StudentProfile, ConceptMastery, AssessmentLog


class StudentRepository:
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "tutor_records.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Create tables and indexes if they do not exist."""
        with self._get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS student_profiles (
                student_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                target_goal TEXT NOT NULL,
                explanation_preference TEXT NOT NULL,
                pace_rate REAL NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS student_concept_mastery (
                student_id TEXT NOT NULL,
                concept_id TEXT NOT NULL,
                mastery REAL NOT NULL,
                confidence REAL NOT NULL,
                attempts_count INTEGER NOT NULL,
                success_count INTEGER NOT NULL,
                last_practiced TEXT,
                next_review_due TEXT,
                active_misconceptions TEXT NOT NULL,
                PRIMARY KEY (student_id, concept_id),
                FOREIGN KEY (student_id) REFERENCES student_profiles(student_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS assessment_logs (
                id TEXT PRIMARY KEY,
                student_id TEXT NOT NULL,
                concept_id TEXT NOT NULL,
                question_asked TEXT NOT NULL,
                student_response TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                score REAL NOT NULL,
                detected_misconceptions TEXT NOT NULL,
                evaluator_feedback TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES student_profiles(student_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS session_cursors (
                student_id TEXT PRIMARY KEY,
                question_indexes TEXT NOT NULL,
                consecutive_failures TEXT NOT NULL,
                last_active_concept TEXT,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES student_profiles(student_id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_assessment_student ON assessment_logs(student_id);
            CREATE INDEX IF NOT EXISTS idx_mastery_student ON student_concept_mastery(student_id);
            """)

    def save_profile(self, profile: StudentProfile) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute("""
            INSERT INTO student_profiles (
                student_id, name, target_goal, explanation_preference, pace_rate, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(student_id) DO UPDATE SET
                name = excluded.name,
                target_goal = excluded.target_goal,
                explanation_preference = excluded.explanation_preference,
                pace_rate = excluded.pace_rate,
                updated_at = excluded.updated_at
            """, (
                profile.student_id,
                profile.name,
                profile.target_goal,
                profile.explanation_preference,
                profile.pace_rate,
                now,
                now
            ))

    def load_profile(self, student_id: str) -> Optional[StudentProfile]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM student_profiles WHERE student_id = ?", (student_id,)
            ).fetchone()
            if not row:
                return None
            return StudentProfile(
                student_id=row["student_id"],
                name=row["name"],
                target_goal=row["target_goal"],
                explanation_preference=row["explanation_preference"],
                pace_rate=row["pace_rate"]
            )

    def list_profiles(self) -> List[StudentProfile]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM student_profiles ORDER BY updated_at DESC").fetchall()
            return [
                StudentProfile(
                    student_id=r["student_id"],
                    name=r["name"],
                    target_goal=r["target_goal"],
                    explanation_preference=r["explanation_preference"],
                    pace_rate=r["pace_rate"]
                ) for r in rows
            ]

    def save_mastery(self, student_id: str, mastery: ConceptMastery) -> None:
        last_prac = mastery.last_practiced.isoformat() if mastery.last_practiced else None
        next_rev = mastery.next_review_due.isoformat() if mastery.next_review_due else None
        misc_json = json.dumps(mastery.active_misconceptions)

        with self._get_connection() as conn:
            conn.execute("""
            INSERT INTO student_concept_mastery (
                student_id, concept_id, mastery, confidence, attempts_count,
                success_count, last_practiced, next_review_due, active_misconceptions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(student_id, concept_id) DO UPDATE SET
                mastery = excluded.mastery,
                confidence = excluded.confidence,
                attempts_count = excluded.attempts_count,
                success_count = excluded.success_count,
                last_practiced = excluded.last_practiced,
                next_review_due = excluded.next_review_due,
                active_misconceptions = excluded.active_misconceptions
            """, (
                student_id,
                mastery.concept_id,
                mastery.mastery,
                mastery.confidence,
                mastery.attempts_count,
                mastery.success_count,
                last_prac,
                next_rev,
                misc_json
            ))

    def load_mastery_map(self, student_id: str) -> Dict[str, ConceptMastery]:
        mastery_map: Dict[str, ConceptMastery] = {}
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM student_concept_mastery WHERE student_id = ?", (student_id,)
            ).fetchall()
            for r in rows:
                last_prac = datetime.fromisoformat(r["last_practiced"]) if r["last_practiced"] else None
                next_rev = datetime.fromisoformat(r["next_review_due"]) if r["next_review_due"] else None
                misc = json.loads(r["active_misconceptions"]) if r["active_misconceptions"] else []

                mastery_map[r["concept_id"]] = ConceptMastery(
                    concept_id=r["concept_id"],
                    mastery=r["mastery"],
                    confidence=r["confidence"],
                    attempts_count=r["attempts_count"],
                    success_count=r["success_count"],
                    last_practiced=last_prac,
                    next_review_due=next_rev,
                    active_misconceptions=misc
                )
        return mastery_map

    def save_assessment_log(self, log: AssessmentLog) -> None:
        misc_json = json.dumps(log.detected_misconceptions)
        timestamp_str = log.timestamp.isoformat()
        with self._get_connection() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO assessment_logs (
                id, student_id, concept_id, question_asked, student_response,
                is_correct, score, detected_misconceptions, evaluator_feedback, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log.id,
                log.student_id,
                log.concept_id,
                log.question_asked,
                log.student_response,
                1 if log.is_correct else 0,
                log.score,
                misc_json,
                log.evaluator_feedback,
                timestamp_str
            ))

    def load_assessment_history(self, student_id: str) -> List[AssessmentLog]:
        logs: List[AssessmentLog] = []
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM assessment_logs WHERE student_id = ? ORDER BY timestamp ASC", (student_id,)
            ).fetchall()
            for r in rows:
                logs.append(AssessmentLog(
                    id=r["id"],
                    student_id=r["student_id"],
                    concept_id=r["concept_id"],
                    question_asked=r["question_asked"],
                    student_response=r["student_response"],
                    is_correct=bool(r["is_correct"]),
                    score=r["score"],
                    detected_misconceptions=json.loads(r["detected_misconceptions"]),
                    evaluator_feedback=r["evaluator_feedback"],
                    timestamp=datetime.fromisoformat(r["timestamp"])
                ))
        return logs

    def save_session_cursor(
        self,
        student_id: str,
        question_indexes: Dict[str, int],
        consecutive_failures: Dict[str, int],
        last_active_concept: Optional[str] = None
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        q_idx_json = json.dumps(question_indexes)
        c_fail_json = json.dumps(consecutive_failures)
        with self._get_connection() as conn:
            conn.execute("""
            INSERT INTO session_cursors (
                student_id, question_indexes, consecutive_failures, last_active_concept, updated_at
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(student_id) DO UPDATE SET
                question_indexes = excluded.question_indexes,
                consecutive_failures = excluded.consecutive_failures,
                last_active_concept = excluded.last_active_concept,
                updated_at = excluded.updated_at
            """, (student_id, q_idx_json, c_fail_json, last_active_concept, now))

    def load_session_cursor(self, student_id: str) -> Dict[str, Any]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM session_cursors WHERE student_id = ?", (student_id,)
            ).fetchone()
            if not row:
                return {"question_indexes": {}, "consecutive_failures": {}, "last_active_concept": None}
            return {
                "question_indexes": json.loads(row["question_indexes"]),
                "consecutive_failures": json.loads(row["consecutive_failures"]),
                "last_active_concept": row["last_active_concept"]
            }

    def reset_student(self, student_id: str) -> None:
        """Completely reset all progress and records for a student."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM student_profiles WHERE student_id = ?", (student_id,))
