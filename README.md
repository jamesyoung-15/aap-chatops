# Ansible Automation Platform (AAP) ChatOps

Python-based ChatOps bridge that connects chat platforms (Slack, Teams, etc.) to Ansible Automation Platform (AAP).

Features:

- Use chat commands to run AAP commands (eg. list pending workflow approvals for today, check status of today's jobs for current user)
- Add scheduled tasks for automated messages/alerts

<!-- Current use cases: -->

Note: This project has only been tested on AAP 2.6 with controller API V2. V1 api calls will NOT work. AAP API calls are brittle to API schema changes so commands may break if platform/api is upgraded.

## Getting Started

### Prerequisites

- Access to AAP API
- AAP Account API token
- [`uv`](https://docs.astral.sh/uv/getting-started/)
- Chat Platform Setup:
  - Slack (app + bot tokens) - requires app with socket mode enabled, see [setup instructions](https://docs.slack.dev/apis/events-api/using-socket-mode/)

### Installation

1. Clone the repo and install the project dependencies.

    ```bash
    git clone git@gitlab.com:jamesy-amfam/aap-chatops
    cd aap-chatops
    uv sync
    ```

2. Setup environment variables

    ```bash
    cp .env.example .env
    ```

    Then fill out required fields `aap_api_token` and `aap_base_url` alongside the chat platform option and credentials.

### Usage

Right now fastest way is to run: `uv run src/aap_chatops/main.py`. Another option is to use the `scripts/run-bot-tmux.sh` to run the bot in a separate tmux session.

## Development

Setup `pre-commit`:

```bash
pre-commit install
```

Run tests:

```bash
uv run pytest
```

Lint and format:

```bash
uv run ruff format src/ tests/
uv run ruff check src/ tests/
```

Type check:

```bash
uv run pyright src/
```
