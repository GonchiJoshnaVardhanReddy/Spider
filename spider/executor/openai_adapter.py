"""OpenAI-compatible chat completions connector."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from spider.executor.adapter_types import AdapterResult, Transport

Message = dict[str, str]


@dataclass(frozen=True)
class OpenAIAdapterConfig:
    """Configuration for OpenAI-compatible chat completions targets."""

    base_url: str
    model: str
    headers: dict[str, str] = field(default_factory=dict)
    api_key: str | None = None
    timeout_seconds: float = 30.0
    retries: int = 3
    chat_path: str = "/v1/chat/completions"


class OpenAIAdapter:
    """HTTP adapter for POST /v1/chat/completions-compatible APIs."""

    def __init__(
        self,
        config: OpenAIAdapterConfig,
        transport: Transport | None = None,
    ) -> None:
        self._config = config
        self._transport = transport or urlopen

    def send(self, history: list[Message]) -> AdapterResult:
        """Send full conversation history to target and return assistant text."""
        url = f"{self._config.base_url.rstrip('/')}{self._config.chat_path}"
        body = {
            "model": self._config.model,
            "messages": history,
        }
        headers = {
            "Content-Type": "application/json",
            **self._config.headers,
        }
        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"

        request = Request(
            url=url,
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
                        response_text=_extract_openai_text(payload),
                        status_code=status_code,
                    )
            except HTTPError as exc:
                should_retry = attempt < retries and exc.code >= 500
                if not should_retry:
                    raise RuntimeError(f"OpenAI adapter request failed: HTTP {exc.code}") from exc
            except (URLError, TimeoutError, OSError) as exc:
                if attempt >= retries:
                    raise RuntimeError("OpenAI adapter request failed after retries.") from exc

        raise RuntimeError("OpenAI adapter request failed after retries.")


def _extract_openai_text(payload: dict[str, object]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("OpenAI adapter response missing choices.")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise ValueError("OpenAI adapter response choice is invalid.")

    message = first_choice.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            return content

    text = first_choice.get("text")
    if isinstance(text, str):
        return text

    raise ValueError("OpenAI adapter response missing assistant content.")
