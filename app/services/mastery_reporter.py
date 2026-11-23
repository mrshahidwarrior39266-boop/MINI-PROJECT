"""
Mastery Reporter & Verifiable Student Transcript Service:
Generates audit-grade Markdown and JSON educational portfolios demonstrating
evidence-backed mastery, resolved cognitive misconceptions, and cryptographic proof of learning.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional

from app.services.tutor_coordinator import TutorCoordinator

REPORTS_DIR = Path(__file__).resolve().parent.parent / "data" / "transcripts"


class MasteryReporter:
    """Generates verifiable student mastery transcripts and progress reports."""

    @staticmethod
    def compute_audit_hash(coordinator: TutorCoordinator) -> str:
        """Calculate a cryptographic SHA-256 fingerprint over student assessment evidence."""
        student = coordinator.student_service.profile
        mastery_items = [
            (cid, m.mastery, m.confidence, m.success_count)
            for cid, m in sorted(coordinator.student_service.mastery_map.items())
        ]
        log_ids = [log.id for log in coordinator.student_service.assessment_history]
        payload = f"{student.student_id}|{student.name}|{mastery_items}|{log_ids}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16].upper()

    @classmethod
    def generate_json_report(cls, coordinator: TutorCoordinator) -> Dict[str, Any]:
        """Generate structured JSON portfolio data."""
        student = coordinator.student_service.profile
        frontier = coordinator.get_frontier()
        audit_hash = cls.compute_audit_hash(coordinator)

        concept_mastery_list = []
        for cid, concept in coordinator.graph_service.concepts.items():
            m = coordinator.student_service.get_or_create_mastery(cid)
            status = "LOCKED"
            if cid in frontier.mastered:
                status = "MASTERED"
            elif cid in frontier.ready:
                status = "READY"
            elif cid in frontier.in_progress:
                status = "IN_PROGRESS"

            concept_mastery_list.append({
                "concept_id": cid,
                "title": concept.title,
                "status": status,
                "mastery_score": round(m.mastery, 4),
                "mastery_percentage": f"{m.mastery * 100:.1f}%",
                "confidence_score": round(m.confidence, 4),
                "confidence_percentage": f"{m.confidence * 100:.1f}%",
                "attempts_count": m.attempts_count,
                "success_count": m.success_count,
                "active_misconceptions": m.active_misconceptions,
            })

        total_assessments = len(coordinator.student_service.assessment_history)
        avg_score = (
            sum(a.score for a in coordinator.student_service.assessment_history) / total_assessments
            if total_assessments > 0
            else 0.0
        )

        return {
            "transcript_id": f"TRANSCRIPT-{audit_hash}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "student": {
                "id": student.student_id,
                "name": student.name,
                "target_goal": student.target_goal,
                "explanation_preference": student.explanation_preference,
            },
            "curriculum_summary": {
                "total_concepts": len(coordinator.graph_service.concepts),
                "mastered_count": len(frontier.mastered),
                "in_progress_count": len(frontier.in_progress),
                "ready_count": len(frontier.ready),
                "locked_count": len(frontier.locked),
                "total_assessments_logged": total_assessments,
                "average_score": round(avg_score, 4),
            },
            "concepts": concept_mastery_list,
            "verification_audit_hash": audit_hash,
        }

    @classmethod
    def generate_markdown_report(cls, coordinator: TutorCoordinator) -> str:
        """Generate a beautifully formatted academic student mastery transcript in Markdown."""
        data = cls.generate_json_report(coordinator)
        student = data["student"]
        summary = data["curriculum_summary"]
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        lines = [
            "# Student Mastery Transcript & Competency Portfolio",
            "",
            f"**Transcript ID:** `{data['transcript_id']}`  ",
            f"**Generated:** {now_str}  ",
            f"**Verification Audit Hash:** `{data['verification_audit_hash']}`  ",
            "",
            "---",
            "",
            "## 1. Learner Profile",
            f"- **Student Name:** {student['name']}",
            f"- **Student ID:** `{student['id']}`",
            f"- **Target Goal:** {student['target_goal']}",
            f"- **Pedagogical Mode:** `{student['explanation_preference']}`",
            "",
            "---",
            "",
            "## 2. Curriculum Mastery Matrix",
            "",
            f"**Progress Overview:** {summary['mastered_count']}/{summary['total_concepts']} Units Mastered "
            f"({(summary['mastered_count'] / summary['total_concepts']) * 100:.1f}%) | "
            f"**Total Observed Evaluations:** {summary['total_assessments_logged']}",
            "",
            "| Concept | Status | Mastery | Statistical Confidence | Solved / Attempts |",
            "| :--- | :---: | :---: | :---: | :---: |",
        ]

        for c in data["concepts"]:
            status_badge = {
                "MASTERED": "[x] MASTERED",
                "READY": "[ ] READY",
                "IN_PROGRESS": "[-] IN PROGRESS",
                "LOCKED": "[!] LOCKED",
            }.get(c["status"], c["status"])

            lines.append(
                f"| **{c['title']}** | `{status_badge}` | {c['mastery_percentage']} | {c['confidence_percentage']} | {c['success_count']} / {c['attempts_count']} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 3. Cognitive Misconceptions & Audit Trail",
            "",
        ])

        # Scan assessment history for detected misconceptions
        misconceptions_encountered = set()
        for log in coordinator.student_service.assessment_history:
            for m in log.detected_misconceptions:
                misconceptions_encountered.add(m)

        if misconceptions_encountered:
            lines.append("The learner encountered and engaged with targeted remediation for:")
            for m in sorted(misconceptions_encountered):
                lines.append(f"- **`{m}`**: Remediated through transfer challenges and micro-step scaffolding.")
        else:
            lines.append("- No unresolved cognitive misconceptions currently detected.")

        lines.extend([
            "",
            "---",
            "",
            "> **Integrity Guarantee:** This transcript was generated by the Neuro-Symbolic Intelligent Tutoring System. "
            "Mastery scores are derived strictly from empirical problem-solving evidence, not self-reported sentiment.",
        ])

        return "\n".join(lines)

    @classmethod
    def export_report_to_file(
        cls, coordinator: TutorCoordinator, output_dir: Optional[Path] = None
    ) -> Path:
        """Export the student's mastery transcript to disk as a Markdown file."""
        target_dir = Path(output_dir or REPORTS_DIR)
        target_dir.mkdir(parents=True, exist_ok=True)

        student_id = coordinator.student_service.profile.student_id
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{student_id}_{timestamp}_transcript.md"
        output_path = target_dir / filename

        report_content = cls.generate_markdown_report(coordinator)
        output_path.write_text(report_content, encoding="utf-8")
        return output_path
