# SPIDER

> Prompt Injection AI Agent

Terminal-first AI security agent focused on authorized prompt injection testing for bug bounty workflows.

## Installation

```bash
cd spider
pip install -e .
```

## Usage

```bash
# Start the agent
spider

# Uninstall the tool
spider --uninstall

# Show version
spider --version
```

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
