# Testing

## Structure

Tests mirror `src/aap_chatops/`:

```
tests/
  conftest.py            shared fixtures
  aap_client/            one file per aap_client.py function group
  aap_commands/          one file per registered command
  aap_alerts/            one file per registered alert task
  models/                model-level property tests
  test_commands.py       command registry/dispatch tests
  test_alerts.py         alert task registry tests
  test_alert_config.py   alerts.yaml parsing and resolution
  test_scheduler.py      catch-up, dedup, failure isolation
  test_state.py          last-fired persistence
  test_formatting.py
  test_settings.py
  test_slack_adapter.py
  test_logging_config.py
```

`aap_client/`, `aap_commands/`, `aap_alerts/`, and `models/` each have an
empty `__init__.py`. Without it, pytest's default import mode would collide
on files with the same basename in different directories (eg.
`aap_client/test_ping.py` and `aap_commands/test_ping.py` would both try
to import as a top-level module named `test_ping`).

Tests that read the repo's own alert config target `alerts.example.yaml`,
not `alerts.yaml`, since the latter is user-created and gitignored.

## Fixtures (`tests/conftest.py`)

- `_clear_registries` (autouse) - clears the global `commands._commands`
  and `alerts._tasks` dicts before and after every test, since both are
  shared mutable state.
- `make_settings` - factory fixture returning a `Settings` builder with
  sane defaults, passing `_env_file=None` so tests never read the
  developer's real `.env`.
- `make_approval_payload`, `make_workflow_job_payload`,
  `make_aap_user_payload` - factory fixtures returning realistic raw API
  response dicts, overridable via kwargs (eg. delete a nested field to
  test a fallback case).

Prefer these fixtures over redefining payloads locally in a test file.

## Mocking approach

Most `aap_client` tests use `httpx.MockTransport` with a synchronous
`handler(request) -> httpx.Response` closure, exercising the real
`httpx.AsyncClient` request/response/parsing pipeline rather than mocking
`aap_client` functions directly. Use `monkeypatch.setattr` only when
isolating a higher-level function's branching logic from HTTP details
(eg. testing `ping_aap_api`'s true/false branches against a stubbed
`get_request`).

## Async tests

`asyncio_mode = "auto"` is set in `pyproject.toml`, so `async def
test_...` functions run without needing `@pytest.mark.asyncio`.

## Running

```
uv run pytest
uv run pyright
uv run ruff check --fix .
uv run ruff format .
```
