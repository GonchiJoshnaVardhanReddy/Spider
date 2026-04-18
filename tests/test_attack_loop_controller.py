"""Attack loop controller orchestration tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from spider.attack_loop.controller import AttackLoopConfig, AttackLoopController


class _PlannerStub:
    def __init__(self, strategies: list[str]) -> None:
        self._strategies = strategies
        self.calls = 0

    def select_strategy(self, previous_response: str | None = None, **_: object) -> str:
        del previous_response
        choice = self._strategies[min(self.calls, len(self._strategies) - 1)]
        self.calls += 1
        return choice


class _RetrieverStub:
    def retrieve_payloads(self, category: str) -> list[dict[str, str]]:
        return [{"prompt": f"{category}-payload"}]


class _EmptyRetrieverStub:
    def retrieve_payloads(self, category: str) -> list[dict[str, str]]:
        del category
        return []


class _RetrieverWithDiagnosticsStub:
    def retrieve_payloads(self, category: str) -> list[dict[str, str | dict[str, object]]]:
        return [
            {
                "prompt": f"{category}-payload",
                "_retriever_diagnostics": {
                    "selected_category": category,
                    "candidate_count": 7,
                    "fallback": "taxonomy:override",
                },
            }
        ]


class _MutatorStub:
    def transform(self, payload: str) -> str:
        return f"mutated::{payload}"


class _ExecutorStub:
    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self.sent_payloads: list[str] = []

    def reset_session(self) -> None:
        self.sent_payloads = []

    def send(self, payload: str) -> dict[str, int | str]:
        self.sent_payloads.append(payload)
        response = self._responses[min(len(self.sent_payloads) - 1, len(self._responses) - 1)]
        return {
            "response_text": response,
            "status_code": 200,
            "latency_ms": 100,
            "session_length": len(self.sent_payloads),
        }


class _EvaluatorStub:
    def __init__(self, verdicts: list[dict[str, bool | float]]) -> None:
        self._verdicts = verdicts
        self.calls = 0

    def evaluate(self, response_text: str) -> dict[str, bool | float]:
        del response_text
        verdict = self._verdicts[min(self.calls, len(self._verdicts) - 1)]
        self.calls += 1
        return verdict


def _failed_verdict(confidence: float = 0.1) -> dict[str, bool | float]:
    return {
        "attack_successful": False,
        "system_prompt_leak_detected": False,
        "policy_leak_detected": False,
        "role_override_detected": False,
        "refusal_bypass_detected": False,
        "tool_misuse_detected": False,
        "context_poisoning_detected": False,
        "confidence_score": confidence,
    }


def _success_verdict(confidence: float = 0.92) -> dict[str, bool | float]:
    out = _failed_verdict(confidence=confidence)
    out["attack_successful"] = True
    out["role_override_detected"] = True
    return out


def test_attack_loop_multi_turn_success_stops_early(tmp_path: Path) -> None:
    controller = AttackLoopController(
        planner=_PlannerStub(["roleplay", "encoding"]),
        retriever=_RetrieverStub(),
        mutator=_MutatorStub(),
        executor=_ExecutorStub(["first response", "second response"]),
        evaluator=_EvaluatorStub([_failed_verdict(), _success_verdict()]),
        config=AttackLoopConfig(max_turns=8, log_path=tmp_path / "attack_loop.log"),
    )

    result = controller.run_attack(target_config={"name": "target-a"})

    assert result["attack_successful"] is True
    assert result["turns"] == 2
    assert result["termination_reason"] == "attack_successful"
    assert result["strategies_used"] == ["roleplay", "encoding"]
    assert len(result["payload_chain"]) == 2
    assert len(result["verdict_chain"]) == 2


def test_attack_loop_terminates_at_max_turns(tmp_path: Path) -> None:
    controller = AttackLoopController(
        planner=_PlannerStub(["roleplay"]),
        retriever=_RetrieverStub(),
        mutator=_MutatorStub(),
        executor=_ExecutorStub(["r1", "r2", "r3"]),
        evaluator=_EvaluatorStub([_failed_verdict(), _failed_verdict(), _failed_verdict()]),
        config=AttackLoopConfig(max_turns=3, log_path=tmp_path / "attack_loop.log"),
    )

    result = controller.run_attack(target_config={"name": "target-b"})

    assert result["attack_successful"] is False
    assert result["turns"] == 3
    assert result["termination_reason"] == "max_turns_reached"


def test_attack_loop_escalates_strategy_after_repeated_failure(tmp_path: Path) -> None:
    controller = AttackLoopController(
        planner=_PlannerStub(["roleplay", "roleplay", "roleplay"]),
        retriever=_RetrieverStub(),
        mutator=_MutatorStub(),
        executor=_ExecutorStub(["r1", "r2", "r3"]),
        evaluator=_EvaluatorStub([_failed_verdict(), _failed_verdict(), _failed_verdict()]),
        config=AttackLoopConfig(
            max_turns=3,
            repeated_strategy_failure_threshold=2,
            fallback_order=("roleplay", "encoding", "indirect_injection", "override"),
            log_path=tmp_path / "attack_loop.log",
        ),
    )

    result = controller.run_attack(target_config={"name": "target-c"})

    strategies = [entry["strategy"] for entry in result["payload_chain"]]
    assert strategies == ["roleplay", "roleplay", "encoding"]
    assert "encoding" in result["strategies_used"]


def test_attack_loop_terminates_on_confidence_threshold(tmp_path: Path) -> None:
    controller = AttackLoopController(
        planner=_PlannerStub(["context_poisoning"]),
        retriever=_RetrieverStub(),
        mutator=_MutatorStub(),
        executor=_ExecutorStub(["single response"]),
        evaluator=_EvaluatorStub([_failed_verdict(confidence=0.95)]),
        config=AttackLoopConfig(
            max_turns=8,
            confidence_threshold=0.9,
            log_path=tmp_path / "attack_loop.log",
        ),
    )

    result = controller.run_attack(target_config={"name": "target-d"})

    assert result["attack_successful"] is False
    assert result["termination_reason"] == "confidence_threshold_reached"
    assert result["final_confidence_score"] == 0.95


def test_attack_loop_writes_log_file(tmp_path: Path) -> None:
    log_path = tmp_path / "attack_loop.log"
    controller = AttackLoopController(
        planner=_PlannerStub(["roleplay"]),
        retriever=_RetrieverStub(),
        mutator=_MutatorStub(),
        executor=_ExecutorStub(["response"]),
        evaluator=_EvaluatorStub([_success_verdict()]),
        config=AttackLoopConfig(max_turns=8, log_path=log_path),
    )

    controller.run_attack(target_config={"name": "target-e"})

    log_text = log_path.read_text(encoding="utf-8").lower()
    assert "strategy selected" in log_text
    assert "payload executed" in log_text
    assert "verdict produced" in log_text
    assert "termination reason" in log_text


def test_attack_loop_retriever_empty_uses_controller_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = AttackLoopController(
        planner=_PlannerStub(["roleplay"]),
        retriever=_EmptyRetrieverStub(),
        mutator=_MutatorStub(),
        executor=_ExecutorStub(["response"]),
        evaluator=_EvaluatorStub([_success_verdict()]),
        config=AttackLoopConfig(max_turns=3, log_path=tmp_path / "attack_loop.log"),
    )
    monkeypatch.setattr(
        controller,
        "_load_random_template_payload",
        lambda strategy: f"{strategy}-fallback",
    )

    result = controller.run_attack(target_config={"name": "target-f"})

    assert result["turns"] == 1
    assert result["payload_chain"][0]["payload"] == "roleplay-fallback"


def test_attack_loop_emits_retriever_diagnostics_event(tmp_path: Path) -> None:
    events: list[dict[str, object]] = []
    controller = AttackLoopController(
        planner=_PlannerStub(["roleplay"]),
        retriever=_RetrieverWithDiagnosticsStub(),
        mutator=_MutatorStub(),
        executor=_ExecutorStub(["response"]),
        evaluator=_EvaluatorStub([_success_verdict()]),
        config=AttackLoopConfig(max_turns=3, log_path=tmp_path / "attack_loop.log"),
    )

    controller.run_attack(
        target_config={
            "name": "target-g",
            "_progress_callback": lambda event: events.append(event),
        }
    )

    diagnostics = next(event for event in events if event.get("event") == "retriever_diagnostics")
    assert diagnostics["category"] == "roleplay"
    assert diagnostics["candidates"] == 7
    assert diagnostics["fallback"] == "taxonomy:override"
