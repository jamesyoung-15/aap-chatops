# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project Guide

### Project Overview

AAP ChatOps acts as a bridge between chat platforms (eg. Slack) and Ansible Automation Platform (AAP), where developers can use chat commands to run AAP commands. It is designed to be chat platform agnostic.

### Project Structure

- `src/aap_chatops` - library code
- `tests` - unit tests
- `docs` - documentation

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
