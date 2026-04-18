"""Termination guards for attack-loop execution."""

from __future__ import annotations


def is_confidence_threshold_reached(verdict: dict[str, object], threshold: float) -> bool:
    """Return True when verdict confidence reaches or exceeds threshold."""
    confidence = verdict.get("confidence_score", 0.0)
    if isinstance(confidence, (float, int)):
        return float(confidence) >= float(threshold)
    return False


def is_max_turns_reached(turn: int, max_turns: int) -> bool:
    """Return True when attack turn count has reached configured maximum."""
    return turn >= max_turns


def is_repeated_strategy_failure(
    *,
    strategy_failures: dict[str, int],
    strategy: str,
    threshold: int,
    fallback_order: tuple[str, ...],
) -> bool:
    """Return True when current and fallback strategies are exhausted by failures."""
    if strategy_failures.get(strategy, 0) < threshold:
        return False
    return all(strategy_failures.get(item, 0) >= threshold for item in fallback_order)
