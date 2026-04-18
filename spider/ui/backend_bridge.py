"""UI-to-backend orchestration bridge for SPIDER attack workflows."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from spider.attack_loop.controller import AttackLoopController
from spider.evaluator.evaluator import Evaluator
from spider.executor.executor import Executor, ExecutorConfig
from spider.memory.strategy_memory import StrategyMemory
from spider.reporting.report_generator import ReportGenerator, sanitize_target_filename

ProgressCallback = Callable[[dict[str, Any]], None]


class SpiderBackendBridge:
    """Connect Textual UI actions to attack loop, memory, and reporting layers."""

    def __init__(
        self,
        *,
        strategy_memory: StrategyMemory | None = None,
        report_generator: ReportGenerator | None = None,
        attack_controller_factory: Callable[
            [dict[str, Any], list[str]], tuple[AttackLoopController, Any]
        ]
        | None = None,
    ) -> None:
        for runtime_dir in (Path("logs"), Path("reports"), Path("memory"), Path("rag")):
            runtime_dir.mkdir(parents=True, exist_ok=True)

        self._strategy_memory = strategy_memory or StrategyMemory()
        self._report_generator = report_generator or ReportGenerator(output_dir=Path("reports"))
        self._attack_controller_factory = (
            attack_controller_factory or self._default_attack_controller_factory
        )
        self._latest_report_paths: dict[str, str] | None = None
        self._latest_result: dict[str, Any] | None = None
        self._active_executor: Any | None = None
        reports_dir = Path(getattr(self._report_generator, "_output_dir", Path("reports")))
        self._reports_markdown_dir = Path(
            getattr(self._report_generator, "_markdown_dir", reports_dir / "markdown")
        )
        self._reports_markdown_dir.mkdir(parents=True, exist_ok=True)

    def run_scan(
        self,
        target_config: dict[str, Any],
        progress_callback: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        """Execute full attack scan and persist memory/report artifacts."""
        normalized = self._normalize_target_config(target_config)
        ranked = self._strategy_memory.get_ranked_strategies(normalized["target_id"])
        controller, executor = self._attack_controller_factory(normalized, ranked)
        self._active_executor = executor

        run_config = dict(normalized)
        if progress_callback is not None:
            run_config["_progress_callback"] = progress_callback

        result = controller.run_attack(target_config=run_config)
        result["target_id"] = normalized["target_id"]

        self._strategy_memory.update(normalized["target_id"], result)
        evaluator_summary = _latest_verdict(result)
        report_paths = self._report_generator.generate_report(
            target_id=normalized["target_id"],
            attack_result=result,
            evaluator_summary=evaluator_summary,
            model_used=str(normalized.get("model", "unknown")),
            strategy_memory=self._strategy_memory,
        )

        self._latest_result = result
        self._latest_report_paths = report_paths

        if progress_callback is not None:
            progress_callback(
                {
                    "event": "report_generated",
                    "report_paths": report_paths,
                }
            )

        return {
            **result,
            "report_paths": report_paths,
        }

    def list_reports(self, limit: int = 10) -> list[str]:
        """Return recent report base names sorted by newest first."""
        report_files = sorted(
            self._reports_markdown_dir.glob("*.md"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        return [path.stem for path in report_files[: max(0, limit)]]

    def load_report_preview(self, target_id: str, max_chars: int = 4000) -> str:
        """Load markdown preview for a target report."""
        safe_name = sanitize_target_filename(target_id)
        report_path = self._reports_markdown_dir / f"{safe_name}.md"
        if not report_path.exists():
            raise FileNotFoundError(f"No report found for target '{target_id}'.")
        text = report_path.read_text(encoding="utf-8")
        return text[:max_chars]

    def export_latest(self, export_type: str) -> str:
        """Return path to latest report artifact of requested format."""
        if self._latest_report_paths is None:
            raise ValueError("No in-session scan result available. Run /scan first.")

        normalized = export_type.strip().lower()
        mapping = {
            "json": "json_path",
            "md": "markdown_path",
            "markdown": "markdown_path",
            "html": "html_path",
        }
        path_key = mapping.get(normalized)
        if path_key is None:
            raise ValueError("Unsupported export format. Use json, md, or html.")
        return self._latest_report_paths[path_key]

    def reset_session(self) -> None:
        """Reset active executor session and clear latest in-memory scan state."""
        if self._active_executor is not None:
            reset = getattr(self._active_executor, "reset_session", None)
            if callable(reset):
                reset()
        self._latest_report_paths = None
        self._latest_result = None

    def _normalize_target_config(self, target_config: dict[str, Any]) -> dict[str, Any]:
        target_id = str(target_config.get("target_id") or target_config.get("target") or "").strip()
        if not target_id:
            raise ValueError("target_id is required for scanning.")

        connector_type = str(target_config.get("connector_type", "openai")).lower()
        normalized: dict[str, Any] = {
            "target_id": target_id,
            "target_url": str(target_config.get("target_url") or target_id),
            "connector_type": connector_type,
            "model": str(target_config.get("model", "target-model")),
            "max_turns": int(target_config.get("max_turns", 8)),
        }
        if "api_key" in target_config:
            normalized["api_key"] = target_config["api_key"]
        return normalized

    def _default_attack_controller_factory(
        self,
        target_config: dict[str, Any],
        ranked_strategies: list[str],
    ) -> tuple[AttackLoopController, Any]:
        planner = _RankedPlanner(ranked_strategies)
        retriever = _RetrieverAdapter()
        mutator = _MutatorAdapter()
        executor = _build_executor_for_target(target_config)
        evaluator = Evaluator()
        controller = AttackLoopController(
            planner=planner,
            retriever=retriever,
            mutator=mutator,
            executor=executor,
            evaluator=evaluator,
        )
        return controller, executor


class _RankedPlanner:
    def __init__(self, ranked_strategies: list[str]) -> None:
        self._ranked = ranked_strategies or ["roleplay", "encoding", "override"]

    def select_strategy(
        self,
        *,
        previous_response: str | None = None,
        previous_verdict: dict[str, Any] | None = None,
        strategy_history: list[str] | None = None,
        turn: int = 1,
    ) -> str:
        del previous_response, previous_verdict
        history = strategy_history or []
        for strategy in self._ranked:
            if strategy not in history:
                return strategy

        idx = max(0, turn - 1)
        if idx < len(self._ranked):
            return self._ranked[idx]
        return self._ranked[-1]


class _RetrieverAdapter:
    def retrieve_payloads(self, category: str) -> list[dict[str, Any]]:
        from spider_retriever import retrieve_payloads_with_diagnostics

        payloads, diagnostics = retrieve_payloads_with_diagnostics(category=category, k=25)
        if not isinstance(payloads, list):
            raise ValueError("Retriever returned unsupported payload set.")
        if payloads and isinstance(payloads[0], dict):
            annotated = dict(payloads[0])
            annotated["_retriever_diagnostics"] = diagnostics
            payloads[0] = annotated
        return payloads


class _MutatorAdapter:
    def transform(self, payload: str) -> str:
        from mutation_engine import random_mutation

        return random_mutation(payload)


def _build_executor_for_target(target_config: dict[str, Any]) -> Executor:
    connector_type = str(target_config.get("connector_type", "openai")).lower()
    if connector_type == "openai":
        api_key = str(target_config.get("api_key") or os.getenv("SPIDER_TARGET_API_KEY", ""))
        config = ExecutorConfig(
            connector_type="openai",
            base_url=str(target_config["target_url"]),
            model=str(target_config.get("model", "target-model")),
            api_key=api_key if api_key else None,
        )
        return Executor(config)

    if connector_type == "rest":
        endpoint_url = str(target_config.get("endpoint_url") or target_config["target_url"])
        config = ExecutorConfig(
            connector_type="rest",
            endpoint_url=endpoint_url,
            auth_token=str(target_config.get("auth_token", "")) or None,
            request_schema_override=dict(target_config.get("request_schema_override", {})),
        )
        return Executor(config)

    raise ValueError(f"Unsupported connector type: {connector_type}")


def _latest_verdict(attack_result: dict[str, Any]) -> dict[str, Any]:
    verdict_chain = attack_result.get("verdict_chain", [])
    if isinstance(verdict_chain, list) and verdict_chain:
        last = verdict_chain[-1]
        if isinstance(last, dict):
            return last
    return {
        "attack_successful": bool(attack_result.get("attack_successful", False)),
        "confidence_score": float(attack_result.get("final_confidence_score", 0.0)),
        "system_prompt_leak_detected": False,
        "policy_leak_detected": False,
        "role_override_detected": False,
        "refusal_bypass_detected": False,
        "tool_misuse_detected": False,
        "context_poisoning_detected": False,
    }
