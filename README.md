# SPIDER

> Prompt Injection AI Agent

Terminal-first AI security agent focused on authorized prompt injection testing for bug bounty workflows.

## Installation

```bash
# 1) Clone the repository
git clone https://github.com/GonchiJoshnaVardhanReddy/Spider.git
cd Spider

# 2) Install (Linux)
python3 -m pip install -e .

# 2) Install (Windows PowerShell)
py -m pip install -e .
```

## Usage

```bash
# Start the agent
spider

# Start via module (works on Linux and Windows)
python -m spider

# Uninstall the tool
spider --uninstall

# Show version
spider --version
```

## Cross-platform notes

- SPIDER is tested to run on both Linux and Windows.
- Prefer `python -m pip ...` / `py -m pip ...` over plain `pip` for consistent behavior across environments.
- If `spider` is not on your PATH, use `python -m spider` instead.

## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/model` | Show or set active model |
| `/clear` | Clear chat history |
| `/history` | Show session history |
| `/export` | Export chat to file |
| `/uninstall` | Uninstall SPIDER package |
| `/exit` | Exit SPIDER |

## What Changed

- Startup intro animation is disabled; the app now opens directly into chat.
- A SPIDER banner is rendered inside the chat section.
- The assistant behavior and messaging are now oriented to prompt injection assessments for LLM targets.

## Scope and Safety

Use SPIDER only on targets you are explicitly authorized to test (for example, in-scope bug bounty programs or internal environments).

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message |
| `Ctrl+L` | Clear screen |
| `Ctrl+C` | Quit |
| `Up/Down` | Navigate input history |

## Project Structure

```
spider/
├── main.py           # Entry point
├── config/           # Configuration
├── core/             # Core functionality
└── ui/
    ├── app.py        # Main application
    ├── layout.py     # Main screen layout
    ├── theme.py      # Colors and CSS
    └── widgets.py    # UI components
```

## Requirements

- Python 3.10+
- Textual
- Rich

## License

MIT
