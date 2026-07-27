# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project Guide

### Project Overview

AAP ChatOps acts as a bridge between chat platforms (eg. Slack) and Ansible Automation Platform (AAP), where developers can use chat commands to run AAP commands. It is designed to be chat platform agnostic.

### Project Structure

- `src/aap_chatops` - library code
  - `models/` - pydantic models for AAP API resources
  - `aap_commands/` - one module per chat command
  - `aap_alerts/` - one module per scheduled alert task
  - `formatting.py` - reply-formatting helpers shared by more than one caller
- `tests` - unit tests, mirrors `src/aap_chatops` structure
- `docs` - documentation
- `scripts` - operational helper scripts (eg. running the bot in tmux)

### Architecture

Commands are registered via a decorator-based registry (`commands.py`) and dispatched by trigger keyword (eg. `!ping`). Each AAP-backed command lives in its own module under `aap_commands/`, exposing a `register(client, settings)` function that closes over the shared HTTP client and settings object rather than using a DI framework. See `docs/architecture.md` for details, and `docs/testing.md` for test conventions.

The bot also posts on a schedule. Alert tasks use the same registry pattern (`alerts.py`, `aap_alerts/`), but a task only builds its message: when and where it posts comes from `alerts.yaml`, bound to the task at startup.

See `docs/adding-a-command.md` and `docs/adding-an-alert.md` for step-by-step guides.

## Coding Standards

### Python Standards

- Always format and check Python files with ruff immediately after writing or editing them: `uv run ruff format <file_path>` and `uv run ruff check --fix <file_path>`
- Use type hints if possible, check type with `uv run pyright`
- Comment sparingly. If using comments, keep comments brief, where code should say what, comments say why

### Git Standards

- When making git commits, use conventional commits, (eg. `feat: allow provided config object to extend other configs`). Keep commit messages brief
- NEVER add agent to author in commit messages
- When creating new git branch, use conventional branch (eg. `feat/login-page`). This project follows trunk-based development, branch off of main

## Writing Style

- No emojis, no em-dashes
- Keep guides and documentation brief, avoid verbose instructions
