"""Executor runtime for multi-turn payload transmission to target LLM endpoints."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from spider.executor.adapter_types import Transport
from spider.executor.openai_adapter import OpenAIAdapter, OpenAIAdapterConfig
from spider.executor.rest_adapter import RESTAdapter, RESTAdapterConfig
from spider.executor.session import ExecutorSession


@dataclass(frozen=True)
class ExecutorConfig:
    """Top-level executor configuration."""

    connector_type: str
    base_url: str | None = None
    model: str | None = None
    endpoint_url: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    api_key: str | None = None
    auth_token: str | None = None
    timeout_seconds: float = 30.0
    retries: int = 3
    request_schema_override: dict[str, Any] = field(default_factory=dict)
    log_path: Path = Path("logs/executor.log")


class Executor:
    """Session-aware payload executor for OpenAI-compatible and REST targets."""

    def __init__(
        self,
        config: ExecutorConfig,
        *,
        session: ExecutorSession | None = None,
        transport: Transport | None = None,
    ) -> None:
        self.config = config
        self.session = session or ExecutorSession()
        self._logger = _build_executor_logger(config.log_path)
        self._connector = self._build_connector(transport)

    def send(self, payload: str) -> dict[str, int | str]:
        """Send payload in-session and return structured execution metadata."""
        if not payload.strip():
            raise ValueError("Executor payload cannot be empty.")

        self.session.add_user_message(payload)
        self._logger.info("Payload sent: %s", payload)

        start = time.perf_counter()
        result = self._connector.send(self.session.history)
        latency_ms = int((time.perf_counter() - start) * 1000)

        self.session.add_assistant_message(result.response_text)
        self._logger.info(
            "Response received: status_code=%s latency_ms=%s",
            result.status_code,
            latency_ms,
        )

        return {
            "response_text": result.response_text,
            "status_code": result.status_code,
            "latency_ms": latency_ms,
            "session_length": len(self.session.history),
        }

    def reset_session(self) -> None:
        """Reset conversation state for a new attack chain or target."""
        self.session.reset()
        self._logger.info("Session reset.")

    def export_transcript(self) -> list[dict[str, str]]:
        """Return a detached copy of the current session transcript."""
        return self.session.export_transcript()

    def _build_connector(self, transport: Transport | None) -> OpenAIAdapter | RESTAdapter:
        connector_type = self.config.connector_type.lower()
        if connector_type == "openai":
            if not self.config.base_url or not self.config.model:
                raise ValueError("OpenAI connector requires base_url and model.")
            return OpenAIAdapter(
                OpenAIAdapterConfig(
                    base_url=self.config.base_url,
                    model=self.config.model,
                    headers=self.config.headers,
                    api_key=self.config.api_key,
                    timeout_seconds=self.config.timeout_seconds,
                    retries=self.config.retries,
                ),
                transport=transport,
            )

        if connector_type == "rest":
            if not self.config.endpoint_url:
                raise ValueError("REST connector requires endpoint_url.")

            schema = self.config.request_schema_override
            history_field = schema.get("history_field", "history")
            if history_field is not None and not isinstance(history_field, str):
                raise ValueError("request_schema_override.history_field must be a string or null.")

            return RESTAdapter(
                RESTAdapterConfig(
                    endpoint_url=self.config.endpoint_url,
                    headers=self.config.headers,
                    auth_token=self.config.auth_token,
                    timeout_seconds=self.config.timeout_seconds,
                    retries=self.config.retries,
                    message_field=str(schema.get("message_field", "message")),
                    history_field=history_field,
                    response_path=str(schema.get("response_path", "response")),
                    static_body=dict(schema.get("static_body", {})),
                ),
                transport=transport,
            )

        raise ValueError(f"Unsupported connector_type: {self.config.connector_type}")


def _build_executor_logger(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger_name = f"spider.executor.{log_path.resolve()}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )
        logger.addHandler(file_handler)

    return logger
