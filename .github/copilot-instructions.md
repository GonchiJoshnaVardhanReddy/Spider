# Copilot Instructions for SPIDER

## Build, test, and lint commands

- **Install (editable package)**  
  - Windows PowerShell: `py -m pip install -e .`  
  - Linux/macOS: `python -m pip install -e .`
- **Install dev extras (includes pytest + pytest-asyncio)**  
  - `py -m pip install -e ".[dev]"`
- **Run the app**  
  - `spider`  
  - `python -m spider`
- **Tests (pytest)**  
  - Full suite: `pytest`  
  - Single test: `pytest path\to\test_file.py::test_name`  
  - Current repository state: no test files are checked in yet.
- **Lint**  
  - No lint tool/config is currently defined in this repository.

## High-level architecture

1. **Startup path**: `spider/main.py` parses CLI args (`--version`, `--uninstall`) and launches `SpiderApp`; `spider/__main__.py` forwards `python -m spider` to the same entry point.
2. **App shell**: `spider/ui/app.py` defines `SpiderApp` and applies shared CSS from `spider/ui/theme.py` (`APP_CSS`), then mounts `MainScreen`.
3. **Main screen flow**: `spider/ui/layout.py` is the central interaction layer. It composes top bar, banner, chat history, input area, and status bar, then routes user input to either slash-command handling (`_handle_command`) or normal message handling (`_handle_message`).
4. **UI components**: `spider/ui/widgets.py` holds reusable Textual widgets (top/status bars, chat messages, thinking indicator, command input with local history, input activity status/hints).
5. **Configuration boundary**: `spider/config/__init__.py` contains app metadata constants (`VERSION`, `APP_NAME`, `TAGLINE`) used across UI and messaging.
6. **Backend status**: `spider/core/` is currently a placeholder; `MainScreen._generate_response` in `spider/ui/layout.py` is the stubbed response path where a real model/backend integration is expected.

## Key conventions in this codebase

- **Textual event/action naming is the control plane**: input and key flows rely on Textual conventions (`on_mount`, `on_command_input_submitted`, `action_*` methods, `Binding(...)` declarations). Preserve these names when adding behavior.
- **Slash commands are centralized in one method**: keep command behavior in `MainScreen._handle_command` and keep command copy aligned with README command docs.
- **Message roles are style contracts**: chat messages use roles (`user`, `assistant`, `system`, `error`) that map to CSS classes in `MessageWidget` via `add_class(f"{role}-message")`; new roles require both behavior and styling updates.
- **Cross-platform pip invocation pattern**: when invoking pip from code, use `sys.executable -m pip ...` (see CLI and `/uninstall` command implementation) rather than shelling out to bare `pip`.
- **Domain framing is explicit in UI/system copy**: messaging is intentionally scoped to authorized prompt-injection assessment workflows; keep new system/help text consistent with that scope.
