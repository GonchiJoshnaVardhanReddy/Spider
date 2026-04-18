"""Backend bridge integration tests for UI attack workflow wiring."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from spider.memory.strategy_memory import StrategyMemory
from spider.reporting.report_generator import ReportGenerator
from spider.ui.backend_bridge import SpiderBackendBridge


class _ExecutorStub:
    def __init__(self) -> None:
        self.reset_called = False

    def reset_session(self) -> None:
        self.reset_called = True


class _ControllerStub:
    def run_attack(self, target_config: dict[str, Any] | None = None) -> dict[str, Any]:
        callback = None
        if isinstance(target_config, dict):
            callback = target_config.get("_progress_callback")
        if callable(callback):
            callback({"event": "scan_started"})
            callback({"event": "strategy_selected", "turn": 1, "strategy": "roleplay"})
            callback({"event": "payload_executed", "turn": 1, "payload": "p1"})
            callback({"event": "verdict_produced", "turn": 1, "verdict": {"confidence_score": 0.92}})
        return {
            "attack_successful": True,
            "turns": 1,
            "final_confidence_score": 0.92,
            "strategies_used": ["roleplay"],
            "payload_chain": [{"turn": 1, "strategy": "roleplay", "payload": "payload one"}],
            "verdict_chain": [
                {
                    "attack_successful": True,
                    "system_prompt_leak_detected": False,
                    "policy_leak_detected": False,
                    "role_override_detected": True,
                    "refusal_bypass_detected": False,
                    "tool_misuse_detected": False,
                    "context_poisoning_detected": False,
                    "confidence_score": 0.92,
                }
            ],
            "termination_reason": "attack_successful",
        }


def test_run_scan_updates_memory_generates_reports_and_emits_events(tmp_path: Path) -> None:
    executor = _ExecutorStub()
    controller = _ControllerStub()

    def factory(
        target_config: dict[str, Any],
        ranked: list[str],
    ) -> tuple[_ControllerStub, _ExecutorStub]:
        assert target_config["target_id"] == "https://api.example.com"
        assert isinstance(ranked, list)
        return controller, executor

    memory = StrategyMemory(data_root=tmp_path / "memory")
    reports = ReportGenerator(output_dir=tmp_path / "reports")
    bridge = SpiderBackendBridge(
        strategy_memory=memory,
        report_generator=reports,
        attack_controller_factory=factory,
    )

    events: list[str] = []
    result = bridge.run_scan(
        {"target_id": "https://api.example.com", "target_url": "https://api.example.com"},
        progress_callback=lambda event: events.append(str(event.get("event"))),
    )

    assert result["attack_successful"] is True
    assert "report_paths" in result
    report_paths = result["report_paths"]
    assert Path(report_paths["json_path"]).exists()
    assert Path(report_paths["markdown_path"]).exists()
    assert Path(report_paths["html_path"]).exists()
    assert "report_generated" in events

    ranked = memory.get_ranked_strategies("https://api.example.com")
    assert ranked[0] == "roleplay"


def test_report_listing_preview_export_and_reset(tmp_path: Path) -> None:
    executor = _ExecutorStub()
    controller = _ControllerStub()

    bridge = SpiderBackendBridge(
        strategy_memory=StrategyMemory(data_root=tmp_path / "memory"),
        report_generator=ReportGenerator(output_dir=tmp_path / "reports"),
        attack_controller_factory=lambda *_: (controller, executor),
    )

    bridge.run_scan({"target_id": "api.example.com", "target_url": "https://api.example.com"})
    names = bridge.list_reports(limit=5)
    assert "api_example_com" in names

    preview = bridge.load_report_preview("api.example.com", max_chars=500)
    assert "SPIDER Vulnerability Report" in preview

    markdown_path = bridge.export_latest("md")
    assert markdown_path.endswith(".md")

    bridge.reset_session()
    assert executor.reset_called is True
