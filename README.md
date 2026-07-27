# Ansible Automation Platform (AAP) ChatOps

Python-based ChatOps bridge that connects chat platforms (Slack, Teams, etc.) to Ansible Automation Platform (AAP).

Features:

- Use chat commands to run AAP commands (eg. list pending workflow approvals for today, check status of today's jobs for current user)
- Get scheduled alerts without asking (eg. a pending approvals summary every weekday morning). Schedules are configured in `alerts.yaml`, and a run missed while the bot was down can optionally be caught up on restart

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

3. Setup scheduled alerts

    ```bash
    cp alerts.example.yaml alerts.yaml
    ```

    Each entry runs a registered alert task on a cron schedule. Set `default_alert_channel_id` in `.env` and invite the bot to that channel, otherwise posts fail with `channel_not_found`. To run without scheduled alerts, set `alerts_enabled=false` instead of creating the file.

    In the cron expression, the day of week must be `*` or names (eg. `mon-fri`, `tue,thu`). Numbers are rejected, see [docs/adding-an-alert.md](docs/adding-an-alert.md).

### Usage

Right now fastest way is to run: `uv run src/aap_chatops/main.py`. Another option is to use the `scripts/run-bot-tmux.sh` to run the bot in a separate tmux session.

One process serves both chat commands and scheduled alerts. Which alert runs have already fired is tracked in `.state/alerts.json`, so restarting the bot does not repost them.

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
