"""Template renderers for markdown and HTML reports."""

from __future__ import annotations

from html import escape
from typing import Any


def render_markdown(report: dict[str, Any]) -> str:
    """Render report dictionary to markdown text."""
    meta = report["metadata"]
    summary = report["attack_summary"]

    payload_timeline = "\n".join(
        f"- **Turn {entry['turn']}** ({entry.get('strategy', 'unknown')}):\n"
        f"  ```\n{entry.get('payload', '')}\n  ```"
        for entry in report["payload_timeline"]
    )

    verdict_lines = "\n".join(
        _markdown_verdict_entry(index + 1, verdict)
        for index, verdict in enumerate(report["verdict_breakdown"])
    )

    reproduction = "\n".join(report["reproduction_steps"])
    strategy_context = ""
    if report.get("strategy_memory_context"):
        strategy_context = (
            "\n## Strategy Memory Context\n\n"
            + "\n".join(
                f"- {name}: {rate:.0%} historical success rate"
                for name, rate in report["strategy_memory_context"].items()
            )
            + "\n"
        )

    return (
        f"# SPIDER Vulnerability Report - {summary['target_id']}\n\n"
        f"- Timestamp: {meta['timestamp']}\n"
        f"- SPIDER Version: {meta['spider_version']}\n"
        f"- Model Used: {meta['model_used']}\n\n"
        "## Attack Summary\n\n"
        f"- Target: {summary['target_id']}\n"
        f"- Turns: {summary['turn_count']}\n"
        f"- Strategies Used: {' -> '.join(summary['strategies_used'])}\n"
        f"- Termination Reason: {summary['termination_reason']}\n"
        f"- Severity: {report['severity_level']}\n"
        f"- Confidence: {report['confidence_score']}\n\n"
        "## Payload Timeline\n\n"
        f"{payload_timeline}\n\n"
        "## Verdict Breakdown\n\n"
        f"{verdict_lines}\n\n"
        "## Reproduction Steps\n\n"
        f"{reproduction}\n"
        f"{strategy_context}"
    )


def render_html(report: dict[str, Any]) -> str:
    """Render report dictionary to simple styled HTML."""
    meta = report["metadata"]
    summary = report["attack_summary"]

    payload_items = "".join(
        "<li><strong>Turn "
        + escape(str(entry["turn"]))
        + "</strong> ("
        + escape(str(entry.get("strategy", "unknown")))
        + ")<pre>"
        + escape(str(entry.get("payload", "")))
        + "</pre></li>"
        for entry in report["payload_timeline"]
    )

    verdict_items = "".join(
        "<li><strong>Turn "
        + escape(str(index + 1))
        + "</strong><pre>"
        + escape(_plain_verdict(verdict))
        + "</pre></li>"
        for index, verdict in enumerate(report["verdict_breakdown"])
    )

    reproduction_items = "".join(f"<li>{escape(step)}</li>" for step in report["reproduction_steps"])
    strategy_rows = "".join(
        f"<li>{escape(name)}: {rate:.0%} historical success rate</li>"
        for name, rate in report.get("strategy_memory_context", {}).items()
    )
    strategy_block = (
        f"<section><h2>Strategy Memory Context</h2><ul>{strategy_rows}</ul></section>"
        if strategy_rows
        else ""
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>SPIDER Vulnerability Report - {escape(summary["target_id"])}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; line-height: 1.5; }}
    section {{ margin-bottom: 1.5rem; }}
    pre {{ background: #f5f5f5; padding: 0.75rem; overflow-x: auto; }}
    .meta {{ color: #555; }}
  </style>
</head>
<body>
  <h1>SPIDER Vulnerability Report</h1>
  <p class="meta">Timestamp: {escape(meta["timestamp"])} | SPIDER Version: {escape(meta["spider_version"])} | Model: {escape(meta["model_used"])}</p>
  <section>
    <h2>Attack Summary</h2>
    <ul>
      <li>Target: {escape(summary["target_id"])}</li>
      <li>Turns: {escape(str(summary["turn_count"]))}</li>
      <li>Strategies Used: {escape(" -> ".join(summary["strategies_used"]))}</li>
      <li>Termination Reason: {escape(summary["termination_reason"])}</li>
      <li>Severity: {escape(report["severity_level"])}</li>
      <li>Confidence: {escape(str(report["confidence_score"]))}</li>
    </ul>
  </section>
  <section>
    <h2>Payload Timeline</h2>
    <ol>{payload_items}</ol>
  </section>
  <section>
    <h2>Verdict Breakdown</h2>
    <ol>{verdict_items}</ol>
  </section>
  <section>
    <h2>Reproduction Steps</h2>
    <ol>{reproduction_items}</ol>
  </section>
  {strategy_block}
</body>
</html>"""


def _markdown_verdict_entry(turn: int, verdict: dict[str, Any]) -> str:
    return (
        f"- **Turn {turn}**\n"
        f"  - attack_successful: {bool(verdict.get('attack_successful', False))}\n"
        f"  - system_prompt_leak_detected: {bool(verdict.get('system_prompt_leak_detected', False))}\n"
        f"  - policy_leak_detected: {bool(verdict.get('policy_leak_detected', False))}\n"
        f"  - role_override_detected: {bool(verdict.get('role_override_detected', False))}\n"
        f"  - refusal_bypass_detected: {bool(verdict.get('refusal_bypass_detected', False))}\n"
        f"  - tool_misuse_detected: {bool(verdict.get('tool_misuse_detected', False))}\n"
        f"  - context_poisoning_detected: {bool(verdict.get('context_poisoning_detected', False))}\n"
        f"  - confidence_score: {verdict.get('confidence_score', 0.0)}"
    )


def _plain_verdict(verdict: dict[str, Any]) -> str:
    keys = [
        "attack_successful",
        "system_prompt_leak_detected",
        "policy_leak_detected",
        "role_override_detected",
        "refusal_bypass_detected",
        "tool_misuse_detected",
        "context_poisoning_detected",
        "confidence_score",
    ]
    lines = [f"{key}: {verdict.get(key, False)}" for key in keys]
    return "\n".join(lines)
