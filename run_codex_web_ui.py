"""
Codex Web UI Launcher:
Starts the ArchaLearn Codex-inspired web server for the Intelligent Tutoring System.
"""
import sys
from pathlib import Path
from app.server import run_server

if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port=port, auto_fallback=True)
