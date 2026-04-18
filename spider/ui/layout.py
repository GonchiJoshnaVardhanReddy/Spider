"""SPIDER main layout - Copilot-style chat interface."""

from __future__ import annotations

import asyncio
import subprocess
import sys
from typing import Any
from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.containers import Container, Vertical, VerticalScroll

from spider.core import SpiderAgentPipeline
from spider.reporting.severity import classify_severity_from_chain
from spider.ui.backend_bridge import SpiderBackendBridge
from spider.ui.widgets import (
    TopBar,
    StatusBar,
    ChatBanner,
    MessageWidget,
    ThinkingWidget,
    CommandInput,
    InputActivityStatus,
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
        Binding("ctrl+r", "reload", "Reset session", show=False),
        Binding("escape", "focus_input", "Focus", show=False),
    ]

    def __init__(self, backend_bridge: SpiderBackendBridge | None = None) -> None:
        super().__init__()
        self._pipeline = SpiderAgentPipeline()
        self._mode = "prompt-injection"
        self._model = self._pipeline.default_model
        self._backend = backend_bridge or SpiderBackendBridge()
        self._last_scan_result: dict[str, Any] | None = None

    def compose(self) -> ComposeResult:
        """Compose the main layout."""
        yield TopBar(mode=self._mode, model=self._model, connected=False, id="top-bar")
        with Vertical(id="main-container"):
            yield ChatBanner(id="chat-banner")
            yield ChatArea(id="chat-area")
            with Container(id="input-container"):
                yield InputActivityStatus(id="input-activity")
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
        input_activity = self.query_one("#input-activity", InputActivityStatus)

        # Add user message
        await chat.add_message(user_input, role="user")

        input_activity.set_activity(self._infer_input_activity(user_input))
        try:
            # Handle commands
            if user_input.startswith("/"):
                await self._handle_command(user_input[1:])
            else:
                await self._handle_message(user_input)
        finally:
            input_activity.clear_activity()

    async def _handle_command(self, command: str) -> None:
        """Process slash commands."""
        chat = self.query_one("#chat-area", ChatArea)
        parts = command.strip().split()
        if not parts:
            await chat.add_message("Empty command. Type /help for available commands.", role="error")
            return
        cmd = parts[0].lower()
        args = command.split()[1:] if len(command.split()) > 1 else []

        if cmd == "help":
            help_text = (
                "Commands:\n\n"
                "/help        Show this help\n"
                "/scan        Run autonomous attack scan on a target\n"
                "/model       Show or set active model\n"
                "/clear       Clear chat history\n"
                "/history     Show recent scan reports\n"
                "/report      Preview report markdown for target\n"
                "/export      Export latest report artifact (json|md|html)\n"
                "/uninstall   Uninstall SPIDER package\n"
                "/exit        Exit SPIDER\n\n"
                "Use this agent only on systems you are authorized to test.\n\n"
                "Shortcuts:\n\n"
                "Ctrl+C       Cancel/Quit\n"
                "Ctrl+L       Clear screen\n"
                "Ctrl+R       Reset scan session\n"
                "Up/Down      Navigate history"
            )
            await chat.add_message(help_text, role="system")

        elif cmd == "scan":
            if not args:
                await chat.add_message("Usage: /scan <target_url>", role="error")
                return
            target = args[0].strip()
            await self._run_scan(target)

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
            reports = self._backend.list_reports(limit=10)
            if not reports:
                await chat.add_message("No scan history found in reports/markdown/.", role="system")
                return
            lines = "\n".join(f"- {name}" for name in reports)
            await chat.add_message(f"Recent scans:\n\n{lines}", role="system")

        elif cmd == "report":
            if not args:
                await chat.add_message("Usage: /report <target>", role="error")
                return
            target = args[0].strip()
            try:
                preview = self._backend.load_report_preview(target, max_chars=3500)
                await chat.add_message(
                    f"Report preview for {target}:\n\n{preview}",
                    role="system",
                )
            except FileNotFoundError as exc:
                await chat.add_message(str(exc), role="error")

        elif cmd == "export":
            if not args:
                await chat.add_message("Usage: /export <json|md|html>", role="error")
                return
            export_type = args[0].strip().lower()
            try:
                path = self._backend.export_latest(export_type)
                await chat.add_message(
                    f"Export ready ({export_type}): {path}",
                    role="system",
                )
            except ValueError as exc:
                await chat.add_message(str(exc), role="error")

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

    async def _run_scan(self, target: str) -> None:
        """Run autonomous scan in worker thread and stream progress events."""
        chat = self.query_one("#chat-area", ChatArea)
        top_bar = self.query_one("#top-bar", TopBar)

        await chat.add_message(f"Starting scan for: {target}", role="system")
        top_bar.set_connected(True)
        await chat.show_thinking()

        target_config = build_target_config(target=target, model=self._model)

        def progress_callback(event: dict[str, Any]) -> None:
            self.app.call_from_thread(self._handle_progress_event, event)

        try:
            result = await asyncio.to_thread(
                self._backend.run_scan,
                target_config,
                progress_callback,
            )
            self._last_scan_result = result
            await self._show_scan_summary(target, result)
        except Exception as exc:
            await chat.add_message(f"Scan failed: {exc}", role="error")
        finally:
            await chat.hide_thinking()
            top_bar.set_connected(False)

    def _handle_progress_event(self, event: dict[str, Any]) -> None:
        """Handle thread-safe progress callback event dispatch."""
        self.run_worker(self._render_progress_event(event))

    async def _render_progress_event(self, event: dict[str, Any]) -> None:
        """Render progress event updates into chat and status bar."""
        chat = self.query_one("#chat-area", ChatArea)
        status = self.query_one("#status-bar", StatusBar)

        event_name = str(event.get("event", ""))
        if event_name == "strategy_selected":
            turn = int(event.get("turn", 0))
            strategy = str(event.get("strategy", "unknown"))
            await chat.add_message(f"[Turn {turn}] [Strategy] {strategy}", role="system")
            status.set_turns(turn)
            return

        if event_name == "payload_executed":
            turn = int(event.get("turn", 0))
            payload = str(event.get("mutated_payload") or event.get("payload") or "")
            preview = payload if len(payload) <= 240 else f"{payload[:240]}..."
            await chat.add_message(f"[Turn {turn}] [Payload] {preview}", role="system")
            return

        if event_name == "retriever_diagnostics":
            category = str(event.get("category", "unknown"))
            raw_candidates = event.get("candidates", 0)
            if isinstance(raw_candidates, (int, float)):
                candidates = int(raw_candidates)
            else:
                candidates = 0
            fallback = str(event.get("fallback", "none"))
            await chat.add_message(f"[Retriever] category={category}", role="system")
            await chat.add_message(f"[Retriever] candidates={candidates}", role="system")
            if fallback != "none":
                await chat.add_message(f"[Retriever] fallback={fallback}", role="system")
            return

        if event_name == "response_received":
            turn = int(event.get("turn", 0))
            executor_result = event.get("executor_result", {})
            response_text = event.get("response_text")
            resolved_response = response_text if isinstance(response_text, str) else ""
            if isinstance(executor_result, dict):
                latency = executor_result.get("latency_ms", 0)
                if isinstance(latency, int):
                    status.set_latency(latency)
                if not resolved_response:
                    candidate = executor_result.get("response_text")
                    if isinstance(candidate, str):
                        resolved_response = candidate

            formatted = format_turn_response(turn, resolved_response)
            await chat.add_message(formatted, role="assistant")
            return

        if event_name == "verdict_produced":
            verdict = event.get("verdict", {})
            if isinstance(verdict, dict):
                confidence = verdict.get("confidence_score", 0.0)
                confidence_value = float(confidence) if isinstance(confidence, (int, float)) else 0.0
                badge = verdict_badge(confidence_value)
                status.set_confidence(confidence_value)
                details = summarize_verdict(verdict)
                await chat.add_message(
                    f"[Verdict] [{badge}] {details}",
                    role="system",
                )
            return

        if event_name == "report_generated":
            paths = event.get("report_paths", {})
            if isinstance(paths, dict):
                md_path = paths.get("markdown_path")
                if isinstance(md_path, str):
                    await chat.add_message(f"[Report] Generated: {md_path}", role="system")
            return

    async def _show_scan_summary(self, target: str, result: dict[str, Any]) -> None:
        """Display final scan summary message."""
        chat = self.query_one("#chat-area", ChatArea)
        status = self.query_one("#status-bar", StatusBar)

        success = bool(result.get("attack_successful", False))
        turns = int(result.get("turns", 0))
        strategies = result.get("strategies_used", [])
        strategy_chain = " -> ".join(str(x) for x in strategies) if isinstance(strategies, list) else "unknown"
        termination = str(result.get("termination_reason", "unknown"))
        confidence = result.get("final_confidence_score", 0.0)
        confidence_value = float(confidence) if isinstance(confidence, (int, float)) else 0.0
        status.set_confidence(confidence_value)
        status.set_turns(turns)

        verdict_chain = result.get("verdict_chain", [])
        evaluator_summary: dict[str, Any]
        if isinstance(verdict_chain, list) and verdict_chain and isinstance(verdict_chain[-1], dict):
            evaluator_summary = verdict_chain[-1]
        else:
            evaluator_summary = {"attack_successful": success, "confidence_score": confidence_value}
        severity = classify_severity_from_chain(evaluator_summary, verdict_chain if isinstance(verdict_chain, list) else [])
        badge = verdict_badge(confidence_value)

        await chat.add_message(
            (
                f"Scan finished for {target}\n\n"
                f"attack_successful: {success}\n"
                f"turns: {turns}\n"
                f"strategies: {strategy_chain}\n"
                f"termination_reason: {termination}\n"
                f"severity: {severity}\n"
                f"confidence: {confidence_value:.2f} [{badge}]"
            ),
            role="assistant",
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
            self._pipeline.placeholder_response(message)
        )

    def _infer_input_activity(self, message: str) -> str:
        """Infer a small activity label from user input."""
        msg = message.lower()
        if msg.startswith("/"):
            return "running command..."

        if any(keyword in msg for keyword in ("read", "open", "view", "check")):
            return "reading..."
        if any(keyword in msg for keyword in ("write", "create", "save", "draft")):
            return "writing..."
        if any(keyword in msg for keyword in ("edit", "update", "change", "fix")):
            return "editing..."
        if any(keyword in msg for keyword in ("delete", "remove", "cleanup")):
            return "deleting..."
        if any(keyword in msg for keyword in ("scan", "test", "analyze")):
            return "scanning..."

        return "thinking..."

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
        """Reset backend scan session and attack state."""
        self._backend.reset_session()
        self._last_scan_result = None
        self.run_worker(self._notify_session_reset())

    async def _notify_session_reset(self) -> None:
        chat = self.query_one("#chat-area", ChatArea)
        top_bar = self.query_one("#top-bar", TopBar)
        top_bar.set_connected(False)
        await chat.add_message("Scan session reset.", role="system")

    def action_focus_input(self) -> None:
        """Focus input field."""
        self.query_one("#command-input", CommandInput).focus()


def build_target_config(target: str, model: str) -> dict[str, Any]:
    """Build normalized target configuration for backend scan calls."""
    return {
        "target_id": target,
        "target_url": target,
        "connector_type": "openai",
        "model": model,
    }


def verdict_badge(confidence_score: float) -> str:
    """Map confidence score to evaluator badge label."""
    if confidence_score > 0.8:
        return "SUCCESS"
    if confidence_score >= 0.4:
        return "PARTIAL"
    return "FAILED"


def summarize_verdict(verdict: dict[str, Any]) -> str:
    """Return concise verdict summary for timeline rendering."""
    detected = [
        key
        for key in (
            "system_prompt_leak_detected",
            "policy_leak_detected",
            "role_override_detected",
            "refusal_bypass_detected",
            "tool_misuse_detected",
            "context_poisoning_detected",
        )
        if bool(verdict.get(key, False))
    ]
    if not detected:
        return "No exploitation signals detected."
    return ", ".join(detected)


def truncate_response_text(response_text: str, max_chars: int = 1200) -> str:
    """Trim long model outputs to keep terminal rendering readable."""
    if len(response_text) <= max_chars:
        return response_text
    return f"{response_text[:max_chars]}...(truncated)"


def format_turn_response(turn: int, response_text: str, max_chars: int = 1200) -> str:
    """Format per-turn executor response for timeline rendering."""
    safe_response = truncate_response_text(response_text or "<empty response>", max_chars=max_chars)
    return f"[Turn {turn}] Response:\n{safe_response}"
