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
| `/scan <target>` | Run autonomous multi-turn prompt-injection scan |
| `/model` | Show or set active model |
| `/clear` | Clear chat history |
| `/history` | Show recent scan report history |
| `/report <target>` | Preview latest markdown report for target |
| `/export <json\|md\|html>` | Export latest in-session report artifact |
| `/uninstall` | Uninstall SPIDER package |
| `/exit` | Exit SPIDER |

## Dataset Intelligence Pipeline

Build the dual-tier dataset intelligence outputs:

```bash
python scripts/dataset_pipeline/dataset_intelligence_builder.py
python scripts/vector_index_builder/build_vector_index.py
```

Generated files:

- `rag/templates/prompts.json`
- `rag/templates/metadata.json`
- `rag/templates/prompts_metadata.json` (legacy compatibility)
- `rag/embeddings/prompts_embeddings.npy`
- `rag/embeddings/prompts.index`
- `rag/templates/category_index.json`
- `rag/mutation_reservoir/mutation_prompts.json`
- `rag/mutation_reservoir/scaffolds.json`
- `rag/taxonomy/categories.json`
- `configs/index_config.json`

## Default Ollama Runtime Roles

SPIDER now ships with role-based runtime model defaults in `spider/core`:

- Planner: `spider-planner` (derived from `deepseek-r1:7b`)
- Mutator: `spider-mutator` (derived from `qwen2.5-coder:7b-instruct`)
- Evaluator: `spider-evaluator` (derived from `llama3.1:8b`)

These roles are wired as the default runtime components in `SpiderAgentPipeline`.

## Executor Connectors

SPIDER now includes session-aware executor connectors in `spider/executor` for multi-turn payload delivery to external LLM targets:

- `OpenAIAdapter` for OpenAI-compatible `/v1/chat/completions` APIs
- `RESTAdapter` for configurable REST chatbot endpoints
- `ExecutorSession` for conversation history and reset/export controls
- `Executor` for connector selection, retries/timeouts, latency tracking, and structured response output

Default executor logs are written to `logs/executor.log`.

## Evaluator Engine

SPIDER includes an evaluator engine in `spider/evaluator` that classifies target responses into structured attack-success verdicts:

- regex-based detection for system prompt leakage, policy leakage, role override, tool misuse, and context poisoning
- refusal-bypass detection across multi-turn response history
- optional local LLM judge (`llama3.1:8b`) for secondary classification
- weighted confidence scoring for planner/reporting consumption

## Attack Loop Controller

SPIDER includes an autonomous attack-loop controller in `spider/attack_loop` that orchestrates:

planner → retriever → mutator → executor → evaluator → repeat

Key behavior:

- multi-turn attack state tracking (turns, payload chain, verdict chain, strategies used)
- dynamic strategy selection with fallback escalation order
- termination guards for attack success, max turns, confidence threshold, and repeated strategy failure
- structured final attack result for planner memory/reporting

Default attack-loop logs are written to `logs/attack_loop.log`.

## Strategy Memory

SPIDER includes persistence-backed adaptive strategy memory in `spider/memory`:

- per-target strategy success/failure statistics (`memory/targets/*.json`)
- per-model-family strategy performance and best/weak strategy lists (`memory/families/*.json`)
- global mutation effectiveness counters (`memory/mutations/global.json`)
- ranked strategy retrieval for planner fallback ordering across sessions

## Reporting Engine

SPIDER includes a reporting engine in `spider/reporting` that converts attack-loop and evaluator outputs into bug-bounty-ready artifacts:

- JSON report export (`reports/json/<target>.json`)
- Markdown report export (`reports/markdown/<target>.md`)
- HTML report export (`reports/html/<target>.html`)
- severity classification from detection signals
- payload timeline, verdict breakdown, reproduction steps, and confidence summary

## UI Layer Integration

The Textual UI is wired to backend orchestration through `spider/ui/backend_bridge.py`:

- `/scan` triggers live attack workflow execution
- timeline events stream into chat (`strategy`, `payload`, `verdict`)
- status/top bars update during active scans
- `/report`, `/export`, and `/history` resolve generated report artifacts
- `Ctrl+R` resets active backend session state

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
repo/
├── spider/                         # Python package
│   ├── main.py
│   ├── core/
│   ├── attack_loop/
│   ├── executor/
│   ├── evaluator/
│   ├── memory/
│   ├── reporting/
│   └── ui/
├── rag/                            # Runtime retrieval assets
│   ├── templates/
│   ├── embeddings/
│   ├── mutation_reservoir/
│   └── taxonomy/
├── datasets_raw/                   # Source and unprocessed corpora
│   ├── external_downloads/
│   └── unprocessed/
├── scripts/
│   ├── vector_index_builder/
│   ├── dataset_pipeline/
│   └── maintenance/
├── configs/
├── logs/
├── reports/
│   ├── json/
│   ├── markdown/
│   └── html/
├── memory/
└── deleted/
```

## Requirements

- Python 3.10+
- Textual
- Rich

## License

MIT
