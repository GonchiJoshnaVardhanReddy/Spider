"""Generic REST chatbot connector with configurable request/response schema."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from spider.executor.adapter_types import AdapterResult, Transport

Message = dict[str, str]


@dataclass(frozen=True)
class RESTAdapterConfig:
    """Configuration for generic REST chat endpoints."""

    endpoint_url: str
    headers: dict[str, str] = field(default_factory=dict)
    auth_token: str | None = None
    timeout_seconds: float = 30.0
    retries: int = 3
    message_field: str = "message"
    history_field: str | None = "history"
    response_path: str = "response"
    static_body: dict[str, object] = field(default_factory=dict)


class RESTAdapter:
    """Adapter for configurable REST chatbot APIs."""

    def __init__(
        self,
        config: RESTAdapterConfig,
        transport: Transport | None = None,
    ) -> None:
        self._config = config
        self._transport = transport or urlopen

    def send(self, history: list[Message]) -> AdapterResult:
        """Send message/history to REST endpoint and parse configured response field."""
        latest_user = _latest_user_message(history)
        body: dict[str, object] = dict(self._config.static_body)
        body[self._config.message_field] = latest_user
        if self._config.history_field:
            body[self._config.history_field] = history

        headers = {
            "Content-Type": "application/json",
            **self._config.headers,
        }
        if self._config.auth_token:
            headers["Authorization"] = f"Bearer {self._config.auth_token}"

        request = Request(
            url=self._config.endpoint_url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        return self._post_with_retries(request)

    def _post_with_retries(self, request: Request) -> AdapterResult:
        retries = max(1, self._config.retries)
        for attempt in range(1, retries + 1):
            try:
                with self._transport(request, timeout=self._config.timeout_seconds) as response:
                    status_code = int(response.getcode())
                    payload = json.loads(response.read().decode("utf-8"))
                    return AdapterResult(
                        response_text=_extract_response_text(payload, self._config.response_path),
                        status_code=status_code,
                    )
            except HTTPError as exc:
                should_retry = attempt < retries and exc.code >= 500
                if not should_retry:
                    raise RuntimeError(f"REST adapter request failed: HTTP {exc.code}") from exc
            except (URLError, TimeoutError, OSError) as exc:
                if attempt >= retries:
                    raise RuntimeError("REST adapter request failed after retries.") from exc

        raise RuntimeError("REST adapter request failed after retries.")


def _latest_user_message(history: list[Message]) -> str:
    for message in reversed(history):
        if message.get("role") == "user":
            content = message.get("content")
            if isinstance(content, str):
                return content
    raise ValueError("REST adapter requires at least one user message in history.")


def _extract_response_text(payload: dict[str, object], response_path: str) -> str:
    current: object = payload
    for segment in response_path.split("."):
        if not isinstance(current, dict) or segment not in current:
            current = None
            break
        current = current[segment]

    if isinstance(current, str):
        return current

    for fallback_key in ("response", "message", "content", "text"):
        value = payload.get(fallback_key)
        if isinstance(value, str):
            return value

    raise ValueError("REST adapter response missing configured text field.")
