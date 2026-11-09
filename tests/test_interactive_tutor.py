"""End-to-end tests for the student-facing CLI."""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLAYTHROUGH = ROOT / "tests" / "data" / "full_playthrough_input.txt"


def run_tutor(input_text: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "interactive_tutor.py")],
        cwd=str(ROOT),
        input=input_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )


def clean_output(result: subprocess.CompletedProcess) -> str:
    combined = result.stdout + result.stderr
    assert result.returncode == 0, combined[-2000:]
    assert "Traceback" not in combined, combined[-3000:]
    return combined


def test_full_playthrough_reaches_completion():
    output = clean_output(run_tutor(PLAYTHROUGH.read_text(encoding="utf-8")))
    assert "ALL CURRICULUM CONCEPTS MASTERED" in output
    assert output.count("MASTERY VERIFIED") == 8


def test_eof_mid_session_ends_cleanly():
    output = clean_output(
        run_tutor("Sam\nthe right side is calculated first, then the result is assigned to x\n")
    )
    assert "SESSION SUMMARY" in output


def test_blank_answer_reprompts_instead_of_quitting():
    output = clean_output(
        run_tutor("Sam\n\nthe right side is calculated first, then the result is assigned to x\n")
    )
    assert "Please type an answer" in output
    assert "Updated Mastery" in output


def test_quit_at_name_prompt():
    output = clean_output(run_tutor("quit\n"))
    assert "Session ended." in output


def test_restart_during_scaffolding():
    output = clean_output(run_tutor("Sam\nno solution\n100\nrestart\n"))
    assert "RESTARTING TUTORING SESSION" in output
    assert "SESSION SUMMARY" in output


def test_remediation_briefing_and_scaffolding():
    output = clean_output(run_tutor("Sam\nno solution\n100\n6\nx\n\nquit\n"))
    assert "TARGETED MISCONCEPTION REMEDIATION" in output
    assert "Confusing Assignment with Algebraic Equality" in output
    assert "GUIDED STEP-BY-STEP SCAFFOLDING" in output
    assert "GUIDED WALKTHROUGH COMPLETE" in output
    assert "CONCEPT CLEARED" not in output


def test_followup_success_awards_progress():
    output = clean_output(run_tutor("Sam\nno solution\n8\n"))
    assert "CORRECT on Follow-Up Challenge" in output
    assert "SESSION SUMMARY" in output


def test_quit_at_scaffold_ends_cleanly():
    output = clean_output(run_tutor("Sam\nno solution\n100\nquit\n"))
    assert "SESSION SUMMARY" in output


def test_eof_at_followup_ends_cleanly():
    output = clean_output(run_tutor("Sam\nno solution\n"))
    assert "SESSION SUMMARY" in output


def test_eof_at_scaffold_ends_cleanly():
    output = clean_output(run_tutor("Sam\nno solution\n100\n"))
    assert "SESSION SUMMARY" in output


def test_space_separated_swap_is_accepted_in_the_cli():
    output = clean_output(
        run_tutor(
            "Sam\n"
            "the right side x + 1 is calculated first, then the result is assigned to x\n"
            "\n"
            "b is 10 because it copied a's value when it was 10\n"
            "\n"
            "b=x x=y y=b\n"
        )
    )
    assert "Your code did not swap" not in output
    assert "MASTERY VERIFIED" in output
    assert output.count("Result: CORRECT") >= 3


def test_restart_detection_is_exact_not_substring():
    from interactive_tutor import is_restart

    assert is_restart("restart")
    assert is_restart("  RESET  ")
    assert not is_restart("reset the counter to zero")
    assert not is_restart("start over with a new value")


def test_unicode_name_does_not_crash():
    output = clean_output(run_tutor("小明\nquit\n"))
    assert "SESSION SUMMARY" in output
    assert "小明" in output


def test_quit_at_continue_prompt_ends_session():
    output = clean_output(
        run_tutor(
            "Sam\n"
            "the right side x + 1 is calculated first, then the result is assigned to x\n"
            "quit\n"
        )
    )
    assert "SESSION SUMMARY" in output
    assert "TUTOR QUESTION 2 of 3" not in output
