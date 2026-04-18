"""File exporters for report outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def export_json(path: Path, payload: dict[str, Any]) -> None:
    """Write report payload as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def export_markdown(path: Path, content: str) -> None:
    """Write report content as markdown."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def export_html(path: Path, content: str) -> None:
    """Write report content as HTML."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
