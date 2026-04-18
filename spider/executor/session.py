"""Conversation session state for multi-turn executor payloads."""

from __future__ import annotations

from dataclasses import dataclass, field

Message = dict[str, str]


@dataclass
class ExecutorSession:
    """In-memory transcript that preserves role/content turn history."""

    history: list[Message] = field(default_factory=list)

    def add_user_message(self, text: str) -> None:
        """Append a user payload turn."""
        self.history.append({"role": "user", "content": text})

    def add_assistant_message(self, text: str) -> None:
        """Append an assistant response turn."""
        self.history.append({"role": "assistant", "content": text})

    def reset(self) -> None:
        """Reset the session to an empty transcript."""
        self.history = []

    def export_transcript(self) -> list[Message]:
        """Return a detached copy of current conversation history."""
        return [dict(message) for message in self.history]
