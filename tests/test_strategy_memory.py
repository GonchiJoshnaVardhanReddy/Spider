"""Strategy memory persistence and ranking tests."""

from __future__ import annotations

import json
from pathlib import Path

from spider.memory.model_family import detect_model_family
from spider.memory.strategy_memory import StrategyMemory


def _attack_result(
    *,
    success: bool,
    confidence: float,
    strategies: list[str],
    payload_chain: list[dict[str, str]] | None = None,
    final_response_text: str = "",
) -> dict[str, object]:
    return {
        "attack_successful": success,
        "turns": len(strategies),
        "final_confidence_score": confidence,
        "strategies_used": strategies,
        "payload_chain": payload_chain or [],
        "verdict_chain": [],
        "termination_reason": "attack_successful" if success else "max_turns_reached",
        "final_response_text": final_response_text,
    }


def test_target_memory_creation_and_strategy_success_update(tmp_path: Path) -> None:
    memory = StrategyMemory(data_root=tmp_path / "data")
    target_id = "https://api.example.com"
    memory.update(
        target_id=target_id,
        attack_result=_attack_result(
            success=True,
            confidence=0.92,
            strategies=["roleplay", "encoding"],
        ),
    )

    target_hash = memory.target_hash(target_id)
    target_file = tmp_path / "data" / "targets" / f"{target_hash}.json"
    assert target_file.exists()

    payload = json.loads(target_file.read_text(encoding="utf-8"))
    assert payload["target_id"] == target_id
    assert payload["strategy_stats"]["roleplay"] == {"success": 1, "fail": 0}
    assert payload["strategy_stats"]["encoding"] == {"success": 1, "fail": 0}


def test_strategy_failure_updates_counts(tmp_path: Path) -> None:
    memory = StrategyMemory(data_root=tmp_path / "data")
    target_id = "https://api.example.com"

    memory.update(
        target_id=target_id,
        attack_result=_attack_result(success=True, confidence=0.9, strategies=["roleplay"]),
    )
    memory.update(
        target_id=target_id,
        attack_result=_attack_result(success=False, confidence=0.2, strategies=["roleplay"]),
    )

    target_file = tmp_path / "data" / "targets" / f"{memory.target_hash(target_id)}.json"
    payload = json.loads(target_file.read_text(encoding="utf-8"))
    assert payload["strategy_stats"]["roleplay"] == {"success": 1, "fail": 1}


def test_mutation_statistics_update_and_global_tracking(tmp_path: Path) -> None:
    memory = StrategyMemory(data_root=tmp_path / "data", mutation_confidence_threshold=0.7)
    target_id = "https://api.example.com"

    memory.update(
        target_id=target_id,
        attack_result=_attack_result(
            success=True,
            confidence=0.84,
            strategies=["encoding"],
            payload_chain=[
                {"mutation_type": "markdown_wrapper"},
                {"mutation_type": "unicode_encoding"},
                {"mutation_type": "markdown_wrapper"},
            ],
        ),
    )
    memory.update(
        target_id=target_id,
        attack_result=_attack_result(
            success=False,
            confidence=0.3,
            strategies=["override"],
            payload_chain=[{"mutation_type": "json_wrapper"}],
        ),
    )

    target_payload = json.loads(
        (tmp_path / "data" / "targets" / f"{memory.target_hash(target_id)}.json").read_text(
            encoding="utf-8"
        )
    )
    global_mutations = json.loads(
        (tmp_path / "data" / "mutations" / "global.json").read_text(encoding="utf-8")
    )

    assert target_payload["mutation_stats"]["markdown_wrapper"] == 2
    assert target_payload["mutation_stats"]["unicode_encoding"] == 1
    assert "json_wrapper" not in target_payload["mutation_stats"]
    assert global_mutations["markdown_wrapper"] == 2
    assert global_mutations["unicode_encoding"] == 1
    assert "json_wrapper" not in global_mutations


def test_model_family_detection_signatures() -> None:
    assert detect_model_family("As an AI language model, I cannot do that.") == "gpt"
    assert detect_model_family("I cannot assist with that request due to policy.") == "claude"
    assert detect_model_family("I'm unable to help with that request.") == "gemini"
    assert detect_model_family("No recognizable signature here.") == "unknown"


def test_strategy_ranking_output_order(tmp_path: Path) -> None:
    memory = StrategyMemory(data_root=tmp_path / "data")
    target_id = "https://api.example.com"

    memory.update(
        target_id=target_id,
        attack_result=_attack_result(success=True, confidence=0.8, strategies=["encoding"]),
    )
    memory.update(
        target_id=target_id,
        attack_result=_attack_result(success=True, confidence=0.8, strategies=["encoding"]),
    )
    memory.update(
        target_id=target_id,
        attack_result=_attack_result(success=True, confidence=0.8, strategies=["roleplay"]),
    )
    memory.update(
        target_id=target_id,
        attack_result=_attack_result(success=False, confidence=0.2, strategies=["roleplay"]),
    )
    memory.update(
        target_id=target_id,
        attack_result=_attack_result(success=False, confidence=0.2, strategies=["override"]),
    )
    memory.update(
        target_id=target_id,
        attack_result=_attack_result(success=False, confidence=0.2, strategies=["override"]),
    )

    ranked = memory.get_ranked_strategies(target_id)
    assert ranked[:3] == ["encoding", "roleplay", "override"]


def test_memory_persists_between_instances(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    target_id = "https://api.example.com"

    first = StrategyMemory(data_root=data_root)
    first.update(
        target_id=target_id,
        attack_result=_attack_result(
            success=True,
            confidence=0.95,
            strategies=["encoding"],
            final_response_text="As an AI language model I can provide details.",
        ),
    )
    first.save()

    second = StrategyMemory(data_root=data_root)
    second.load()
    ranked = second.get_ranked_strategies(target_id)

    assert ranked[0] == "encoding"
    family_file = data_root / "families" / "gpt.json"
    assert family_file.exists()
