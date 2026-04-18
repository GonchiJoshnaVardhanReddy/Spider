"""Reporting engine generation and formatting tests."""

from __future__ import annotations

import json
from pathlib import Path

from spider.reporting.report_generator import ReportGenerator, sanitize_target_filename
from spider.reporting.severity import classify_severity


def _sample_attack_result() -> dict[str, object]:
    return {
        "attack_successful": True,
        "turns": 3,
        "final_confidence_score": 0.92,
        "strategies_used": ["roleplay", "encoding"],
        "payload_chain": [
            {"turn": 1, "strategy": "roleplay", "payload": "payload one"},
            {"turn": 2, "strategy": "encoding", "payload": "payload two"},
            {"turn": 3, "strategy": "encoding", "payload": "payload three"},
        ],
        "verdict_chain": [
            {"attack_successful": False, "role_override_detected": True, "confidence_score": 0.6},
            {"attack_successful": True, "system_prompt_leak_detected": True, "confidence_score": 0.92},
        ],
        "termination_reason": "attack_successful",
    }


def _sample_evaluator_summary() -> dict[str, object]:
    return {
        "attack_successful": True,
        "system_prompt_leak_detected": True,
        "policy_leak_detected": False,
        "role_override_detected": True,
        "refusal_bypass_detected": False,
        "tool_misuse_detected": False,
        "context_poisoning_detected": False,
        "confidence_score": 0.92,
    }


def test_json_markdown_and_html_reports_are_created(tmp_path: Path) -> None:
    generator = ReportGenerator(output_dir=tmp_path)
    result = generator.generate_report(
        target_id="https://api.example.com/v1",
        attack_result=_sample_attack_result(),
        evaluator_summary=_sample_evaluator_summary(),
        model_used="spider-evaluator",
    )

    assert Path(result["json_path"]).exists()
    assert Path(result["markdown_path"]).exists()
    assert Path(result["html_path"]).exists()


def test_severity_classification_correctness() -> None:
    severity = classify_severity(
        {
            "attack_successful": True,
            "system_prompt_leak_detected": False,
            "policy_leak_detected": True,
            "tool_misuse_detected": False,
            "role_override_detected": False,
            "refusal_bypass_detected": False,
            "context_poisoning_detected": False,
        }
    )
    assert severity == "HIGH"


def test_payload_timeline_formatting_present_in_markdown(tmp_path: Path) -> None:
    generator = ReportGenerator(output_dir=tmp_path)
    result = generator.generate_report(
        target_id="api.example.com",
        attack_result=_sample_attack_result(),
        evaluator_summary=_sample_evaluator_summary(),
    )
    markdown = Path(result["markdown_path"]).read_text(encoding="utf-8")
    assert "## Payload Timeline" in markdown
    assert "Turn 1" in markdown
    assert "payload one" in markdown
    assert "Turn 2" in markdown
    assert "payload two" in markdown


def test_filename_sanitization() -> None:
    assert sanitize_target_filename("api.example.com") == "api_example_com"
    assert sanitize_target_filename("https://api.example.com/v1?env=prod") == "https_api_example_com_v1_env_prod"
    assert sanitize_target_filename("___") == "report"


def test_json_report_contains_expected_sections(tmp_path: Path) -> None:
    generator = ReportGenerator(output_dir=tmp_path)
    result = generator.generate_report(
        target_id="api.example.com",
        attack_result=_sample_attack_result(),
        evaluator_summary=_sample_evaluator_summary(),
    )
    payload = json.loads(Path(result["json_path"]).read_text(encoding="utf-8"))

    assert payload["metadata"]["target_id"] == "api.example.com"
    assert payload["severity_level"] == "CRITICAL"
    assert payload["attack_summary"]["turn_count"] == 3
    assert len(payload["payload_timeline"]) == 3
    assert len(payload["verdict_breakdown"]) == 2
    assert payload["reproduction_steps"][0].startswith("1. Send payload:")
    assert payload["confidence_score"] == 0.92


def test_strategy_memory_context_is_included_when_available(tmp_path: Path) -> None:
    class _MemoryStub:
        def get_strategy_success_rates(self, target_id: str) -> dict[str, float]:
            assert target_id == "api.example.com"
            return {"encoding": 0.73}

    generator = ReportGenerator(output_dir=tmp_path)
    result = generator.generate_report(
        target_id="api.example.com",
        attack_result=_sample_attack_result(),
        evaluator_summary=_sample_evaluator_summary(),
        strategy_memory=_MemoryStub(),
    )
    payload = json.loads(Path(result["json_path"]).read_text(encoding="utf-8"))
    assert payload["strategy_memory_context"]["encoding"] == 0.73
