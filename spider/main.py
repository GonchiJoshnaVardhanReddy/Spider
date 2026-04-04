"""SPIDER entry point."""

from __future__ import annotations

import argparse
import subprocess
import sys

from spider.config import VERSION


def _uninstall() -> int:
    """Uninstall SPIDER from the current Python environment."""
    command = [sys.executable, "-m", "pip", "uninstall", "-y", "spider"]
    return subprocess.run(command).returncode


def main() -> None:
    """Entry point for SPIDER CLI."""
    parser = argparse.ArgumentParser(
        description="SPIDER - Prompt Injection AI Agent"
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall SPIDER from the current environment",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"SPIDER v{VERSION}",
    )

    args = parser.parse_args()
    if args.uninstall:
        raise SystemExit(_uninstall())

    from spider.ui.app import SpiderApp

    app = SpiderApp()
    app.run()


if __name__ == "__main__":
    main()
