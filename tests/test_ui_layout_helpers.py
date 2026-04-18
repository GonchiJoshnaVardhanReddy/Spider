"""UI layout helper tests for scan integration rendering logic."""

from __future__ import annotations

from spider.ui.layout import (
    build_target_config,
    format_turn_response,
    summarize_verdict,
    truncate_response_text,
    verdict_badge,
)


def test_build_target_config_defaults() -> None:
    config = build_target_config("https://api.example.com", "spider-planner")
    assert config["target_id"] == "https://api.example.com"
    assert config["target_url"] == "https://api.example.com"
    assert config["connector_type"] == "openai"
    assert config["model"] == "spider-planner"


def test_verdict_badge_thresholds() -> None:
    assert verdict_badge(0.95) == "SUCCESS"
    assert verdict_badge(0.6) == "PARTIAL"
    assert verdict_badge(0.2) == "FAILED"


def test_summarize_verdict_detected_signals() -> None:
    verdict = {
        "role_override_detected": True,
        "tool_misuse_detected": True,
    }
    text = summarize_verdict(verdict)
    assert "role_override_detected" in text
    assert "tool_misuse_detected" in text


def test_summarize_verdict_no_detection() -> None:
    assert summarize_verdict({"attack_successful": False}) == "No exploitation signals detected."


def test_truncate_response_text_limits_output() -> None:
    text = "A" * 1300
    truncated = truncate_response_text(text, max_chars=1200)
    assert len(truncated) == 1214
    assert truncated.endswith("...(truncated)")


def test_format_turn_response_includes_turn_and_body() -> None:
    rendered = format_turn_response(turn=2, response_text="target output", max_chars=1200)
    assert rendered.startswith("[Turn 2] Response:\n")
    assert rendered.endswith("target output")
