# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**INTELECTO** is a personal AI assistant built in Python 3.11+. It runs locally on macOS, communicates via Telegram (long-polling), stores memories in SQLite FTS5, and talks to LLMs through OpenRouter or Ollama. The full specification lives in `doc/antidote.md`.

> Status: v0.1.0 — 35 files, 3,412 lines target. **No Python code written yet — implementation in progress.**

## Commands

```bash
# Setup and run
./start.sh                          # One-command launcher: creates venv, installs, runs
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
intelecto                           # Runs wizard if no config, else starts bot
intelecto setup                     # Force reconfigure (runs wizard.py)
python -m intelecto                 # Equivalent to `intelecto` CLI

# Tests (pytest + pytest-asyncio for async tests)
python -m pytest tests/ -v
python -m pytest tests/test_config.py -v   # Single test file

# Logs and process management
tail -f ~/.intelecto/logs/intelecto.log
tail -f ~/.intelecto/audit.log
launchctl list | grep intelecto
launchctl stop com.intelecto.agent
launchctl start com.intelecto.agent
launchctl unload ~/Library/LaunchAgents/com.intelecto.agent.plist
```

Config is generated at `~/.intelecto/config.json` (gitignored). Secrets go to `~/.intelecto/.secrets` (Fernet-encrypted). Memory DB at `~/.intelecto/memory.db`. Identity workspace at `~/.intelecto/workspace/`.

## Architecture

```
Telegram (long-polling)
    → channels/telegram.py → IncomingMessage
    → agent/loop.py (tool-calling loop, max 5 rounds)
        → agent/context.py (assembles system prompt from SOUL/AGENTS/USER.md + memory search)
        → providers/openrouter.py or providers/ollama.py → LLMResponse
        → tools/registry.py dispatches tool calls
        → memory/store.py (SQLite FTS5 save/search)
    → channels/telegram.py → send OutgoingMessage
```

Every subsystem is built on abstract base classes — new providers, channels, tools, and memory backends plug in by implementing the interface, without touching existing code.

## Interface Contracts

All modules MUST implement their abstract base. Do not break these signatures.

**Provider** (`intelecto/providers/base.py`): `async chat(messages, tools, model, temperature) -> LLMResponse`

**Channel** (`intelecto/channels/base.py`): `async start(on_message)`, `async send(OutgoingMessage)`, `async stop()`

**Memory** (`intelecto/memory/store.py`): `async save(content, category)`, `async search(query, limit)`, `async forget(id)`, `async recent(limit)`

**Tool** (`intelecto/tools/base.py`): class attributes `name`, `description`, `parameters` (JSON Schema) + `async execute(**kwargs) -> ToolResult`

See `doc/antidote.md` for the full dataclass definitions (`Message`, `LLMResponse`, `IncomingMessage`, `OutgoingMessage`, `MemoryEntry`, `ToolResult`).

## Identity Stack

Personality is defined by markdown files in `workspace/` (installed to `~/.intelecto/workspace/` at runtime, seeded by wizard):
- `SOUL.md` — core personality
- `AGENTS.md` — tool use and behavior rules
- `USER.md` — user profile and preferences
- `MEMORY.md` — bootstrap facts loaded at first run

These are loaded by `agent/context.py` to build the system prompt on every message.

## Entry Points

- `intelecto/main.py` — CLI router. `intelecto` with no args auto-detects missing config and launches wizard. Exposes `cli()` function.
- `intelecto/__main__.py` — enables `python -m intelecto`, calls `cli()`.
- `wizard.py` — interactive setup wizard (NOT `setup.py` — pip treats `setup.py` as a build script, which conflicts).
- `start.sh` — shell launcher: creates venv if missing, installs deps, runs wizard if no config, starts bot.
- `com.intelecto.agent.plist` — macOS launchd plist for auto-restart on login/crash. Wizard installs it to `~/Library/LaunchAgents/`.

## Security

- API keys stored in `~/.intelecto/.secrets` via Fernet encryption, keyed to macOS hardware UUID (machine-tied, useless if copied)
- `security/safety.py` enforces a command blocklist (`rm -rf /`, `mkfs`, `dd if=`, etc.) and path traversal protection
- Filesystem tools restricted to workspace directory; shell output truncated to 10KB; file reads capped at 100KB
- Max 60s timeout per shell command; audit log at `~/.intelecto/audit.log`
- `config.json` and `.secrets` are gitignored

## Design Constraints (Do Not Violate)

- **No Docker** — Mac-only personal use, not needed
- **No web UI** — Telegram is the only interface
- **No vector/embedding search** — SQLite FTS5 keyword search only
- **No multi-user logic** — single owner
- **No cross-platform abstractions** — macOS launchd for auto-restart
- **Modular by file addition** — new features add files, not edit existing modules

## Build Phases

Phase A (parallel): W1 Config/Secrets → W2 Providers, W3 Memory/Identity, W4 Telegram channel
Phase B: Agent loop, main entry point, wizard
Phase C: pyproject.toml, branding, README, packaging

Full workstream breakdown with task-level detail is in `doc/antidote.md`.
