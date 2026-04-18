"""Structured vulnerability report generation for SPIDER attack outcomes."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from re import sub
from typing import Any

from spider import __version__
from spider.reporting.exporters import export_html, export_json, export_markdown
from spider.reporting.severity import classify_severity_from_chain
from spider.reporting.templates import render_html, render_markdown


class ReportGenerator:
    """Generate JSON, markdown, and HTML reports from attack-loop outputs."""

    def __init__(self, output_dir: Path = Path("reports")) -> None:
        self._output_dir = output_dir
        self._json_dir = self._output_dir / "json"
        self._markdown_dir = self._output_dir / "markdown"
        self._html_dir = self._output_dir / "html"
        self._json_dir.mkdir(parents=True, exist_ok=True)
        self._markdown_dir.mkdir(parents=True, exist_ok=True)
        self._html_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        target_id: str,
        attack_result: dict[str, Any],
        evaluator_summary: dict[str, Any],
        *,
        model_used: str = "unknown",
        strategy_memory: object | None = None,
    ) -> dict[str, str]:
        """Build and export report artifacts for a target."""
        if not target_id.strip():
            raise ValueError("target_id must be a non-empty string.")

        safe_name = sanitize_target_filename(target_id)
        report_json_path = self._json_dir / f"{safe_name}.json"
        report_md_path = self._markdown_dir / f"{safe_name}.md"
        report_html_path = self._html_dir / f"{safe_name}.html"

        payload_timeline = _build_payload_timeline(attack_result.get("payload_chain", []))
        verdict_breakdown = _build_verdict_breakdown(attack_result.get("verdict_chain", []))
        reproduction_steps = _build_reproduction_steps(payload_timeline)
        confidence = _extract_confidence(attack_result, evaluator_summary)
        severity = classify_severity_from_chain(evaluator_summary, verdict_breakdown)

        summary = {
            "target_id": target_id,
            "turn_count": int(attack_result.get("turns", len(payload_timeline))),
            "strategies_used": _extract_strategies(attack_result),
            "termination_reason": str(attack_result.get("termination_reason", "unknown")),
            "confidence_score": confidence,
        }

        strategy_context = _extract_strategy_memory_context(
            strategy_memory=strategy_memory,
            target_id=target_id,
        )

        report_payload: dict[str, Any] = {
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "target_id": target_id,
                "spider_version": __version__,
                "model_used": model_used,
            },
            "attack_summary": summary,
            "severity_level": severity,
            "confidence_score": confidence,
            "attack_result": attack_result,
            "evaluator_summary": evaluator_summary,
            "payload_timeline": payload_timeline,
            "verdict_breakdown": verdict_breakdown,
            "reproduction_steps": reproduction_steps,
            "strategy_memory_context": strategy_context,
        }

        export_json(report_json_path, report_payload)
        export_markdown(report_md_path, render_markdown(report_payload))
        export_html(report_html_path, render_html(report_payload))

        return {
            "json_path": str(report_json_path),
            "markdown_path": str(report_md_path),
            "html_path": str(report_html_path),
        }


def sanitize_target_filename(target_id: str) -> str:
    """Convert target identifier into filesystem-safe report base name."""
    cleaned = sub(r"[^A-Za-z0-9]+", "_", target_id).strip("_")
    return cleaned if cleaned else "report"


def _build_payload_timeline(payload_chain: Any) -> list[dict[str, Any]]:
    if not isinstance(payload_chain, list):
        return []

    timeline: list[dict[str, Any]] = []
    for index, entry in enumerate(payload_chain, start=1):
        if not isinstance(entry, dict):
            continue

        payload = entry.get("payload")
        if not isinstance(payload, str):
            payload = ""
        strategy = entry.get("strategy")
        if not isinstance(strategy, str):
            strategy = "unknown"

        turn = entry.get("turn")
        if not isinstance(turn, int):
            turn = index

        timeline.append(
            {
                "turn": turn,
                "strategy": strategy,
                "payload": payload,
                "mutated_payload": entry.get("mutated_payload"),
            }
        )
    return timeline


def _build_verdict_breakdown(verdict_chain: Any) -> list[dict[str, Any]]:
    if not isinstance(verdict_chain, list):
        return []
    out: list[dict[str, Any]] = []
    for verdict in verdict_chain:
        if isinstance(verdict, dict):
            out.append(dict(verdict))
    return out


def _build_reproduction_steps(payload_timeline: list[dict[str, Any]]) -> list[str]:
    steps: list[str] = []
    for idx, entry in enumerate(payload_timeline, start=1):
        payload = entry.get("payload", "")
        steps.append(f"{idx}. Send payload: {payload}")
    return steps


def _extract_confidence(
    attack_result: dict[str, Any],
    evaluator_summary: dict[str, Any],
) -> float:
    result_confidence = attack_result.get("final_confidence_score")
    if isinstance(result_confidence, (int, float)):
        return float(result_confidence)
    eval_confidence = evaluator_summary.get("confidence_score")
    if isinstance(eval_confidence, (int, float)):
        return float(eval_confidence)
    return 0.0


def _extract_strategies(attack_result: dict[str, Any]) -> list[str]:
    raw = attack_result.get("strategies_used", [])
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        if isinstance(item, str):
            out.append(item)
    return out


def _extract_strategy_memory_context(
    *,
    strategy_memory: object | None,
    target_id: str,
) -> dict[str, float]:
    if strategy_memory is None:
        return {}
    getter = getattr(strategy_memory, "get_strategy_success_rates", None)
    if not callable(getter):
        return {}
    rates = getter(target_id)
    if not isinstance(rates, dict):
        return {}
    out: dict[str, float] = {}
    for key, value in rates.items():
        if isinstance(key, str) and isinstance(value, (float, int)):
            out[key] = float(value)
    return out
