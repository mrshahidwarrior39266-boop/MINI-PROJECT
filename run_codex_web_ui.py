"""
Codex Tutor — Web UI Launcher
Clean, modern runner for the intelligent tutoring system.
"""
import argparse
import sys
from app.server import run_server


def parse_args():
    parser = argparse.ArgumentParser(
        description="Launch the Codex Tutor web interface.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "port_pos",
        nargs="?",
        type=int,
        default=None,
        help="Optional port number (e.g. 8000)",
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8000,
        help="Port to bind server to",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Automatically open web interface in default browser",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    target_port = args.port_pos if args.port_pos is not None else args.port
    run_server(port=target_port, auto_fallback=True, open_browser=args.open)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
