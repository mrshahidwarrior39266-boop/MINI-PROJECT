"""Test running the Milestone 3 demo script end-to-end."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_milestone3_demo_executes_cleanly():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "run_milestone3_demo.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    combined = proc.stdout + proc.stderr
    assert proc.returncode == 0, combined[-2000:]
    assert "MILESTONE 3 DEMO COMPLETE" in combined
    assert "MANDATORY CITATIONS" in combined
    assert "Traceback" not in combined
