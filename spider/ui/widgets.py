"""SPIDER reusable UI widgets."""

from __future__ import annotations

from datetime import datetime

from textual.widgets import Static, Input
from textual.message import Message
from rich.text import Text

from spider.ui.theme import COLORS, LOGO
from spider.config import VERSION, APP_NAME


class TopBar(Static):
    """Top status bar with mode, model, and connection info."""

    DEFAULT_CSS = """
    TopBar {
        width: 100%;
        height: 1;
        background: #111111;
        border-bottom: solid #2a2a2a;
    }
    """

    def __init__(
        self,
        mode: str = "chat",
        model: str = "local",
        connected: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._mode = mode
        self._model = model
        self._connected = connected

    def on_mount(self) -> None:
        """Render top bar."""
        self._render()

    def set_mode(self, mode: str) -> None:
        """Update current mode."""
        self._mode = mode
        self._render()

    def set_model(self, model: str) -> None:
        """Update active model."""
        self._model = model
        self._render()

    def set_connected(self, connected: bool) -> None:
        """Update connection status."""
        self._connected = connected
        self._render()

    def _render(self) -> None:
        """Render the top bar content."""
        text = Text()
        
        # App name
        text.append(f" {APP_NAME} ", style=f"bold {COLORS['accent']}")
        text.append("│", style=COLORS["border"])
        
        # Mode
        text.append(f" {self._mode} ", style=COLORS["text"])
        text.append("│", style=COLORS["border"])
        
        # Model
        text.append(f" {self._model} ", style=COLORS["text_dim"])
        text.append("│", style=COLORS["border"])
        
        # Status
        if self._connected:
            text.append(" ready ", style=COLORS["success"])
        else:
            text.append(" offline ", style=COLORS["text_muted"])
        
        self.update(text)


class StatusBar(Static):
    """Bottom status bar with session info."""

    DEFAULT_CSS = """
    StatusBar {
        width: 100%;
        height: 1;
        background: #111111;
        border-top: solid #2a2a2a;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._tokens = 0
        self._latency = 0

    def on_mount(self) -> None:
        """Render status bar."""
        self._render()

    def set_tokens(self, count: int) -> None:
        """Update token count."""
        self._tokens = count
        self._render()

    def set_latency(self, ms: int) -> None:
        """Update latency."""
        self._latency = ms
        self._render()

    def _render(self) -> None:
        """Render status bar content."""
        text = Text()
        text.append(f" tokens: {self._tokens} ", style=COLORS["text_muted"])
        text.append("│", style=COLORS["border"])
        text.append(f" latency: {self._latency}ms ", style=COLORS["text_muted"])
        text.append("│", style=COLORS["border"])
        text.append(f" v{VERSION} ", style=COLORS["text_muted"])
        self.update(text)


class ChatBanner(Static):
    """Static banner shown above the chat history."""

    DEFAULT_CSS = """
    ChatBanner {
        width: 100%;
        height: auto;
        background: #0d0d0d;
        border-bottom: solid #2a2a2a;
        padding: 1 2;
    }
    """

    def on_mount(self) -> None:
        """Render prompt-injection banner."""
        text = Text()
        for line in LOGO.splitlines():
            text.append(line)
            text.append("\n")
        text.append("Prompt Injection AI Agent for authorized bug bounty testing.", style=COLORS["text_dim"])
        self.update(text)


class MessageWidget(Static):
    """A single message in the chat history."""

    DEFAULT_CSS = """
    MessageWidget {
        width: 100%;
        height: auto;
        padding: 1 2;
        margin: 0 0 1 0;
    }

    MessageWidget.user-message {
        background: #141414;
        border-left: thick #6c6c6c;
    }

    MessageWidget.assistant-message {
        background: #111111;
        border-left: thick #c41e3a;
    }

    MessageWidget.system-message {
        background: #0d0d0d;
        border-left: thick #4a4a4a;
    }

    MessageWidget.error-message {
        background: #1a1010;
        border-left: thick #c41e3a;
    }
    """

    def __init__(
        self,
        content: str,
        role: str = "assistant",
        timestamp: datetime | None = None,
    ) -> None:
        super().__init__()
        self._content = content
        self._role = role
        self._timestamp = timestamp or datetime.now()
        self.add_class(f"{role}-message")

    def on_mount(self) -> None:
        """Render message content."""
        text = Text()
        time_str = self._timestamp.strftime("%H:%M")
        
        # Header
        if self._role == "user":
            text.append("> ", style=COLORS["text_dim"])
            text.append("you", style=f"bold {COLORS['text_dim']}")
        elif self._role == "assistant":
            text.append("> ", style=COLORS["accent"])
            text.append("agent", style=f"bold {COLORS['accent']}")
        elif self._role == "system":
            text.append("> ", style=COLORS["text_muted"])
            text.append("system", style=f"bold {COLORS['text_muted']}")
        elif self._role == "error":
            text.append("> ", style=COLORS["error"])
            text.append("error", style=f"bold {COLORS['error']}")
        
        text.append(f"  {time_str}\n", style=COLORS["text_muted"])
        
        # Content - handle code blocks
        text.append(self._content, style=COLORS["text"])
        
        self.update(text)


class ThinkingWidget(Static):
    """Animated thinking indicator."""

    DEFAULT_CSS = """
    ThinkingWidget {
        width: 100%;
        height: 3;
        padding: 1 2;
        background: #111111;
        border-left: thick #c41e3a;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._frame = 0
        self._dots = ""

    def on_mount(self) -> None:
        """Start animation."""
        self.set_interval(0.15, self._animate)

    def _animate(self) -> None:
        """Update animation frame."""
        self._frame = (self._frame + 1) % 4
        dots = "." * self._frame
        
        text = Text()
        text.append("> ", style=COLORS["accent"])
        text.append("agent", style=f"bold {COLORS['accent']}")
        text.append("  thinking", style=COLORS["text_dim"])
        text.append(dots.ljust(3), style=COLORS["text_dim"])
        self.update(text)


class CommandInput(Input):
    """Chat input with command support."""

    DEFAULT_CSS = """
    CommandInput {
        width: 100%;
        height: 3;
        background: #141414;
        border: tall #2a2a2a;
        padding: 0 1;
    }

    CommandInput:focus {
        border: tall #3a3a3a;
    }

    CommandInput > .input--placeholder {
        color: #4a4a4a;
    }
    """

    class Submitted(Message):
        """Message when input is submitted."""
        def __init__(self, value: str) -> None:
            super().__init__()
            self.value = value

    def __init__(self, **kwargs) -> None:
        super().__init__(placeholder="Describe a prompt-injection test case...", **kwargs)
        self._history: list[str] = []
        self._history_index = -1

    def action_submit(self) -> None:
        """Submit input."""
        value = self.value.strip()
        if value:
            self._history.append(value)
            self._history_index = len(self._history)
            self.post_message(self.Submitted(value))
            self.value = ""

    def key_up(self) -> None:
        """Navigate history up."""
        if self._history and self._history_index > 0:
            self._history_index -= 1
            self.value = self._history[self._history_index]
            self.cursor_position = len(self.value)

    def key_down(self) -> None:
        """Navigate history down."""
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self.value = self._history[self._history_index]
            self.cursor_position = len(self.value)
        elif self._history_index == len(self._history) - 1:
            self._history_index = len(self._history)
            self.value = ""


class InputHint(Static):
    """Keyboard shortcut hints."""

    DEFAULT_CSS = """
    InputHint {
        width: 100%;
        height: 1;
        color: #4a4a4a;
    }
    """

    def on_mount(self) -> None:
        """Render hints."""
        text = Text()
        hints = [
            ("Enter", "send"),
            ("Ctrl+L", "clear"),
            ("Ctrl+C", "quit"),
            ("/help", "commands"),
        ]
        for i, (key, action) in enumerate(hints):
            if i > 0:
                text.append("  ", style=COLORS["text_muted"])
            text.append(key, style=COLORS["text_dim"])
            text.append(f" {action}", style=COLORS["text_muted"])
        self.update(text)
