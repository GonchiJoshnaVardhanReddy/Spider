"""SPIDER main layout - Copilot-style chat interface."""

from __future__ import annotations

import asyncio
import subprocess
import sys
from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.containers import Container, Vertical, VerticalScroll

from spider.ui.widgets import (
    TopBar,
    StatusBar,
    ChatBanner,
    MessageWidget,
    ThinkingWidget,
    CommandInput,
    InputHint,
)


class ChatArea(VerticalScroll):
    """Scrollable chat history."""

    DEFAULT_CSS = """
    ChatArea {
        width: 100%;
        height: 1fr;
        background: #0a0a0a;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._thinking: ThinkingWidget | None = None

    async def add_message(
        self,
        content: str,
        role: str = "assistant",
    ) -> MessageWidget:
        """Add a message to the chat."""
        msg = MessageWidget(content=content, role=role)
        await self.mount(msg)
        msg.scroll_visible()
        return msg

    async def show_thinking(self) -> None:
        """Show thinking indicator."""
        if self._thinking is None:
            self._thinking = ThinkingWidget()
            await self.mount(self._thinking)
            self._thinking.scroll_visible()

    async def hide_thinking(self) -> None:
        """Hide thinking indicator."""
        if self._thinking:
            await self._thinking.remove()
            self._thinking = None

    async def clear(self) -> None:
        """Clear all messages."""
        await self.remove_children()


class MainScreen(Screen):
    """Main chat interface screen."""

    DEFAULT_CSS = """
    MainScreen {
        background: #0a0a0a;
    }

    #main-container {
        width: 100%;
        height: 100%;
    }

    #input-container {
        width: 100%;
        height: auto;
        background: #111111;
        border-top: solid #2a2a2a;
        padding: 1 2;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear_chat", "Clear", show=True),
        Binding("ctrl+k", "command_palette", "Commands", show=False),
        Binding("ctrl+r", "reload", "Reload", show=False),
        Binding("escape", "focus_input", "Focus", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._mode = "prompt-injection"
        self._model = "local"

    def compose(self) -> ComposeResult:
        """Compose the main layout."""
        yield TopBar(mode=self._mode, model=self._model, id="top-bar")
        with Vertical(id="main-container"):
            yield ChatBanner(id="chat-banner")
            yield ChatArea(id="chat-area")
            with Container(id="input-container"):
                yield CommandInput(id="command-input")
                yield InputHint(id="input-hint")
        yield StatusBar(id="status-bar")

    async def on_mount(self) -> None:
        """Initialize with welcome message."""
        chat = self.query_one("#chat-area", ChatArea)
        await chat.add_message(
            "Agent ready for authorized prompt injection assessments. Type /help for commands.",
            role="system"
        )
        self.query_one("#command-input", CommandInput).focus()

    async def on_command_input_submitted(self, event: CommandInput.Submitted) -> None:
        """Handle user input."""
        user_input = event.value
        chat = self.query_one("#chat-area", ChatArea)

        # Add user message
        await chat.add_message(user_input, role="user")

        # Handle commands
        if user_input.startswith("/"):
            await self._handle_command(user_input[1:])
        else:
            await self._handle_message(user_input)

    async def _handle_command(self, command: str) -> None:
        """Process slash commands."""
        chat = self.query_one("#chat-area", ChatArea)
        cmd = command.lower().split()[0]
        args = command.split()[1:] if len(command.split()) > 1 else []

        if cmd == "help":
            help_text = (
                "Commands:\n\n"
                "/help        Show this help\n"
                "/model       Show or set active model\n"
                "/clear       Clear chat history\n"
                "/history     Show session history\n"
                "/export      Export chat to file\n"
                "/uninstall   Uninstall SPIDER package\n"
                "/exit        Exit SPIDER\n\n"
                "Use this agent only on systems you are authorized to test.\n\n"
                "Shortcuts:\n\n"
                "Ctrl+C       Cancel/Quit\n"
                "Ctrl+L       Clear screen\n"
                "Ctrl+K       Command palette\n"
                "Up/Down      Navigate history"
            )
            await chat.add_message(help_text, role="system")

        elif cmd == "clear":
            await chat.clear()
            await chat.add_message("Chat cleared.", role="system")

        elif cmd == "model":
            if args:
                new_model = args[0]
                self._model = new_model
                top_bar = self.query_one("#top-bar", TopBar)
                top_bar.set_model(new_model)
                await chat.add_message(f"Model set to: {new_model}", role="system")
            else:
                await chat.add_message(f"Current model: {self._model}", role="system")

        elif cmd == "history":
            await chat.add_message(
                "History feature not yet implemented.",
                role="system"
            )

        elif cmd == "export":
            await chat.add_message(
                "Export feature not yet implemented.",
                role="system"
            )

        elif cmd == "uninstall":
            await chat.add_message(
                "Running uninstall: pip uninstall -y spider",
                role="system",
            )
            result = subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", "-y", "spider"],
                capture_output=True,
                text=True,
            )
            output = (result.stdout or "").strip()
            errors = (result.stderr or "").strip()
            details = output if output else errors
            if result.returncode == 0:
                await chat.add_message(
                    f"Uninstall complete.\n\n{details or 'SPIDER removed from the current environment.'}",
                    role="system",
                )
            else:
                await chat.add_message(
                    f"Uninstall failed.\n\n{details or 'pip returned a non-zero exit code.'}",
                    role="error",
                )

        elif cmd == "exit" or cmd == "quit":
            self.app.exit()

        else:
            await chat.add_message(
                f"Unknown command: /{cmd}\nType /help for available commands.",
                role="error"
            )

    async def _handle_message(self, message: str) -> None:
        """Process regular chat message."""
        chat = self.query_one("#chat-area", ChatArea)
        status = self.query_one("#status-bar", StatusBar)

        # Show thinking
        await chat.show_thinking()

        # Simulate processing
        await asyncio.sleep(0.8)

        # Hide thinking
        await chat.hide_thinking()

        # Generate response
        response = self._generate_response(message)
        await chat.add_message(response, role="assistant")

        # Update stats
        status.set_tokens(len(message.split()) * 2)
        status.set_latency(150)

    def _generate_response(self, message: str) -> str:
        """Generate a response (placeholder for AI integration)."""
        msg_lower = message.lower()

        if "scan" in msg_lower:
            return (
                "Prompt injection test workflow:\n\n"
                "1. Define target model and guardrails\n"
                "2. Build benign and adversarial prompt sets\n"
                "3. Execute attack variants and log responses\n"
                "4. Score bypass severity and impact\n"
                "5. Produce bug bounty evidence package\n\n"
                "Share the model, scope, and policy objective to begin."
            )

        if "help" in msg_lower or "what can" in msg_lower:
            return (
                "I can assist with:\n\n"
                "- Prompt injection scenario design\n"
                "- Attack payload drafting\n"
                "- Safety bypass evaluation\n"
                "- Logging and report structuring for bug bounty\n"
                "- Mitigation recommendations\n\n"
                "Describe your target and objective."
            )

        return (
            f"Processing: {message}\n\n"
            "This is a prompt-injection agent placeholder response. "
            "Connect your model backend in spider/core for real execution."
        )

    def action_quit(self) -> None:
        """Exit application."""
        self.app.exit()

    def action_clear_chat(self) -> None:
        """Clear chat history."""
        self.run_worker(self._clear_chat())

    async def _clear_chat(self) -> None:
        """Clear chat async."""
        chat = self.query_one("#chat-area", ChatArea)
        await chat.clear()
        await chat.add_message("Chat cleared.", role="system")

    def action_command_palette(self) -> None:
        """Show command palette (placeholder)."""
        pass

    def action_reload(self) -> None:
        """Reload (placeholder)."""
        pass

    def action_focus_input(self) -> None:
        """Focus input field."""
        self.query_one("#command-input", CommandInput).focus()
