"""SPIDER intro animation - Professional spider drop sequence."""

from __future__ import annotations

import asyncio
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static
from textual.containers import Container, Center, Middle
from rich.text import Text

from spider.ui.theme import COLORS, LOGO
from spider.config import VERSION, TAGLINE


class AnimationCanvas(Static):
    """Canvas for rendering the spider drop animation."""

    DEFAULT_CSS = """
    AnimationCanvas {
        width: 100%;
        height: 100%;
        background: #0a0a0a;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._width = 80
        self._height = 24
        self._spider_y = 0
        self._spider_x = 0
        self._thread_length = 0
        self._phase = "drop"  # drop, walk, logo
        self._walk_x = 0
        self._logo_opacity = 0
        self._frame = 0

    def on_mount(self) -> None:
        """Initialize canvas dimensions."""
        self._width = self.size.width or 80
        self._height = self.size.height or 24
        self._spider_x = self._width // 2
        self._target_y = self._height // 2 - 2

    def render_frame(self) -> Text:
        """Render current animation frame."""
        lines = []
        
        if self._phase == "drop":
            lines = self._render_drop()
        elif self._phase == "walk":
            lines = self._render_walk()
        elif self._phase == "logo":
            lines = self._render_logo()
        
        text = Text()
        for line in lines:
            text.append(line + "\n")
        return text

    def _render_drop(self) -> list[str]:
        """Render spider dropping on thread."""
        lines = [""] * self._height
        center_x = self._width // 2
        
        # Draw thread from top to spider
        for y in range(min(self._thread_length, self._height)):
            if y < len(lines):
                line = list(" " * self._width)
                if center_x < len(line):
                    line[center_x] = "│"
                lines[y] = "".join(line)
        
        # Draw spider at current position
        if self._spider_y < self._height:
            spider_chars = ["╱◯╲", " ┼ ", "╱ ╲"]
            for i, row in enumerate(spider_chars):
                y = self._spider_y + i
                if 0 <= y < self._height:
                    line = list(lines[y] if lines[y] else " " * self._width)
                    start_x = center_x - 1
                    for j, char in enumerate(row):
                        x = start_x + j
                        if 0 <= x < self._width:
                            line[x] = char
                    lines[y] = "".join(line)
        
        return lines

    def _render_walk(self) -> list[str]:
        """Render spider walking off screen."""
        lines = [""] * self._height
        center_x = self._width // 2
        spider_y = self._target_y
        
        # Thread stays visible
        for y in range(spider_y):
            line = list(" " * self._width)
            if center_x < len(line):
                line[center_x] = "│"
            lines[y] = "".join(line)
        
        # Walking spider
        walk_frame = self._frame % 2
        if walk_frame == 0:
            spider = ["╱◯╲", "─┼─", "╱ ╲"]
        else:
            spider = ["╲◯╱", "─┼─", "╲ ╱"]
        
        x_pos = center_x + self._walk_x
        for i, row in enumerate(spider):
            y = spider_y + i
            if 0 <= y < self._height:
                line = list(lines[y] if lines[y] else " " * self._width)
                start_x = x_pos - 1
                for j, char in enumerate(row):
                    x = start_x + j
                    if 0 <= x < self._width:
                        line[x] = char
                lines[y] = "".join(line)
        
        return lines

    def _render_logo(self) -> list[str]:
        """Render logo with fade-in effect."""
        logo_lines = LOGO.strip().split("\n")
        logo_height = len(logo_lines)
        logo_width = max(len(line) for line in logo_lines)
        
        # Center logo
        start_y = (self._height - logo_height - 6) // 2
        start_x = (self._width - logo_width) // 2
        
        lines = [""] * self._height
        
        # Render logo
        for i, logo_line in enumerate(logo_lines):
            y = start_y + i
            if 0 <= y < self._height:
                padding = " " * max(0, start_x)
                lines[y] = padding + logo_line
        
        # Add hanging spider on the 'R' of SPIDER
        spider_y = start_y - 1
        spider_x = start_x + logo_width - 8
        if 0 <= spider_y < self._height:
            line = list(lines[spider_y] if lines[spider_y] else " " * self._width)
            if spider_x < self._width:
                line[spider_x] = "│"
            lines[spider_y] = "".join(line)
        
        spider_y = start_y
        if 0 <= spider_y < self._height and spider_x < self._width - 2:
            line = list(lines[spider_y])
            while len(line) < self._width:
                line.append(" ")
            line[spider_x - 1:spider_x + 2] = list("╲●╱")
            lines[spider_y] = "".join(line)
        
        # Tagline
        tagline = f"SPIDER v{VERSION}  |  {TAGLINE}"
        tagline_y = start_y + logo_height + 2
        if 0 <= tagline_y < self._height:
            padding = " " * ((self._width - len(tagline)) // 2)
            lines[tagline_y] = padding + tagline
        
        # Prompt
        prompt = "Type a task to begin"
        prompt_y = tagline_y + 2
        if 0 <= prompt_y < self._height:
            padding = " " * ((self._width - len(prompt)) // 2)
            lines[prompt_y] = padding + prompt
        
        return lines

    async def animate(self, on_complete: callable) -> None:
        """Run the full animation sequence."""
        # Phase 1: Spider drops
        self._phase = "drop"
        drop_speed = 0.03
        
        while self._spider_y < self._target_y:
            self._spider_y += 1
            self._thread_length = self._spider_y + 1
            self.update(self.render_frame())
            await asyncio.sleep(drop_speed)
        
        await asyncio.sleep(0.2)
        
        # Phase 2: Spider walks right
        self._phase = "walk"
        walk_distance = self._width // 2 + 5
        walk_speed = 0.025
        
        while self._walk_x < walk_distance:
            self._walk_x += 1
            self._frame += 1
            self.update(self.render_frame())
            await asyncio.sleep(walk_speed)
        
        await asyncio.sleep(0.1)
        
        # Phase 3: Show logo
        self._phase = "logo"
        self.update(self.render_frame())
        
        await asyncio.sleep(1.0)
        
        on_complete()


class IntroScreen(Screen):
    """Professional intro screen with spider animation."""

    DEFAULT_CSS = """
    IntroScreen {
        background: #0a0a0a;
    }
    """

    BINDINGS = [
        ("escape", "skip", "Skip"),
        ("enter", "skip", "Skip"),
        ("space", "skip", "Skip"),
    ]

    def __init__(self, on_complete: callable | None = None) -> None:
        super().__init__()
        self._on_complete = on_complete
        self._skipped = False
        self._canvas: AnimationCanvas | None = None

    def compose(self) -> ComposeResult:
        """Create the animation canvas."""
        self._canvas = AnimationCanvas()
        yield self._canvas

    async def on_mount(self) -> None:
        """Start the animation."""
        if self._canvas:
            self.run_worker(self._run_animation())

    async def _run_animation(self) -> None:
        """Run animation with skip detection."""
        await asyncio.sleep(0.1)  # Let screen render
        
        if self._skipped:
            self._complete()
            return
        
        if self._canvas:
            await self._canvas.animate(on_complete=self._complete)

    def action_skip(self) -> None:
        """Skip the intro."""
        self._skipped = True
        self._complete()

    def _complete(self) -> None:
        """Transition to main screen."""
        if self._on_complete:
            self._on_complete()
