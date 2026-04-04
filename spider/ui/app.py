"""SPIDER main application."""

from __future__ import annotations

from textual.app import App

from spider.ui.theme import APP_CSS
from spider.ui.layout import MainScreen


class SpiderApp(App):
    """Main SPIDER application."""

    TITLE = "SPIDER Prompt Injection Agent"
    CSS = APP_CSS

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        """Initialize application."""
        self.push_screen(MainScreen())

    def action_quit(self) -> None:
        """Exit application."""
        self.exit()
