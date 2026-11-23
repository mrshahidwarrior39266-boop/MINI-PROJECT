"""
Automated Test for Milestone 2 Demo Script.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_milestone2_demo_runs_flawlessly():
    res = subprocess.run(
        [sys.executable, str(ROOT / "run_milestone2_demo.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    combined = res.stdout + res.stderr
    assert res.returncode == 0, combined[-1000:]
    assert "PART 1: DENSE SEMANTIC VECTOR RETRIEVAL" in combined
    assert "PART 2: GROUNDED SOCRATIC LLM EVALUATION" in combined
    assert "PART 3: PURE COMPUTATIONAL LOGIC VERIFIER" in combined
    assert "PART 4: DYNAMIC Socratic TRANSFER QUESTION GENERATION" in combined
    assert "PART 5: FAULT-TOLERANT OFFLINE FALLBACK GUARANTEE" in combined
    assert "MILESTONE 2 DEMO COMPLETE: ALL SUBSYSTEMS OPERATIONAL" in combined
