"""Shared adapter protocol and result types for executor connectors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
from urllib.request import Request

Transport = Callable[[Request, float], Any]


@dataclass(frozen=True)
class AdapterResult:
    """Normalized connector response returned to the executor."""

    response_text: str
    status_code: int
