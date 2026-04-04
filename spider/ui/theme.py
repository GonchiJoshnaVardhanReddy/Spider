# SPIDER theme configuration - Professional dark security aesthetic.

# Color palette - Red/Grey/White on dark
COLORS = {
    "bg_dark": "#0a0a0a",
    "bg_panel": "#111111",
    "bg_surface": "#1a1a1a",
    "bg_input": "#141414",
    "bg_hover": "#1f1f1f",
    "accent": "#c41e3a",
    "accent_dim": "#8b1528",
    "accent_bright": "#dc3545",
    "text": "#e0e0e0",
    "text_dim": "#6c6c6c",
    "text_muted": "#4a4a4a",
    "text_bright": "#ffffff",
    "success": "#4a9f4a",
    "warning": "#d4a017",
    "error": "#c41e3a",
    "info": "#5a7a9a",
    "border": "#2a2a2a",
    "border_focus": "#3a3a3a",
    "code_bg": "#0d0d0d",
    "code_border": "#252525",
}

# ASCII Art Logo
LOGO_LINES = [
    "███████╗██████╗ ██╗██████╗ ███████╗██████╗ ",
    "██╔════╝██╔══██╗██║██╔══██╗██╔════╝██╔══██╗",
    "███████╗██████╔╝██║██║  ██║█████╗  ██████╔╝",
    "╚════██║██╔═══╝ ██║██║  ██║██╔══╝  ██╔══██╗",
    "███████║██║     ██║██████╔╝███████╗██║  ██║",
    "╚══════╝╚═╝     ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝",
]
LOGO = "\n".join(LOGO_LINES)

# Minimal spider character
SPIDER_MINI = "●"

# Web thread character
WEB_THREAD = "│"

# Textual CSS theme
APP_CSS = """
* {
    scrollbar-background: #111111;
    scrollbar-color: #2a2a2a;
    scrollbar-color-hover: #3a3a3a;
    scrollbar-color-active: #c41e3a;
}

Screen {
    background: #0a0a0a;
}

.top-bar {
    width: 100%;
    height: 1;
    background: #111111;
    color: #6c6c6c;
    border-bottom: solid #2a2a2a;
}

.chat-container {
    width: 100%;
    height: 1fr;
    background: #0a0a0a;
}

.message {
    width: 100%;
    padding: 1 2;
    margin: 0 0 1 0;
}

.message-user {
    background: #141414;
    border-left: thick #6c6c6c;
}

.message-assistant {
    background: #111111;
    border-left: thick #c41e3a;
}

.message-system {
    background: #0d0d0d;
    border-left: thick #4a4a4a;
    color: #6c6c6c;
}

.input-container {
    width: 100%;
    height: auto;
    background: #111111;
    border-top: solid #2a2a2a;
    padding: 1 2;
}

.chat-input {
    width: 100%;
    height: auto;
    min-height: 3;
    background: #141414;
    border: tall #2a2a2a;
    padding: 0 1;
}

.chat-input:focus {
    border: tall #3a3a3a;
}

.status-bar {
    width: 100%;
    height: 1;
    background: #111111;
    color: #4a4a4a;
    border-top: solid #2a2a2a;
}
"""
