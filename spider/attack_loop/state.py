"""State models for autonomous multi-turn attack-loop execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AttackState:
    """Mutable attack-loop runtime state across planner/executor/evaluator turns."""

    turn: int = 0
    strategy: str | None = None
    payloads: list[dict[str, Any]] = field(default_factory=list)
    verdicts: list[dict[str, Any]] = field(default_factory=list)
    executor_results: list[dict[str, Any]] = field(default_factory=list)
    strategies_used: list[str] = field(default_factory=list)
    success: bool = False
    termination_reason: str | None = None
    target_config: dict[str, Any] = field(default_factory=dict)
