# Adding a new command

Steps to add a new `!<name>` chat command. Uses a hypothetical `!jobstatus <id>`
command as a running example.

## 1. Add a model (if the AAP endpoint is new)

If the command needs data from an AAP endpoint not already modeled, add a
file under `src/aap_chatops/models/`:

```python
# src/aap_chatops/models/job.py
from pydantic import BaseModel


class Job(BaseModel):
    id: int
    name: str
    status: str
```

Only model the fields the app actually uses. If the endpoint returns a
paginated list, parse it as `AapListResponse[Job]` (from `models/base.py`)
rather than adding a new envelope type.

## 2. Add an `aap_client.py` function

Add one function per endpoint. Return the parsed model, or `None` on any
failure. Never raise to the caller; log instead.

```python
async def get_job(
    httpx_client: httpx.AsyncClient, aap_api_url: str, job_id: int
) -> Job | None:
    """Fetch a single job by id."""
    response = await get_request(httpx_client, f"{aap_api_url}/jobs/{job_id}/")
    if response is None:
        return None

    try:
        return Job.model_validate(response.json())
    except ValidationError as exc:
        logger.error("Unexpected response shape from jobs endpoint: %s", exc)
        return None
```

Test it in `tests/aap_client/test_<name>.py` using `httpx.MockTransport`
(see `tests/aap_client/test_ping.py` for the simplest example). Cover the
success case, an HTTP error, and an unexpected response shape.

## 3. Add a command module

Create `src/aap_chatops/aap_commands/<name>.py`. Every command module
exposes a `register(client, settings)` function and defines its handler
inside it, so the handler closes over `client`/`settings`. Pass a short
`description` to `@command(...)`, it shows up in `!help`:

```python
"""!jobstatus command: shows the status of a single job."""

import httpx

from aap_chatops.aap_client import get_job
from aap_chatops.commands import CommandContext, command
from aap_chatops.settings import Settings


def register(client: httpx.AsyncClient, settings: Settings) -> None:
    """Register the !jobstatus command, binding the shared client/settings into the handler."""

    @command("jobstatus", description="Show the status of a job by id")
    async def handle_jobstatus(ctx: CommandContext) -> str:
        job_id = _parse_job_id(ctx.raw_text)
        if job_id is None:
            return "Usage: !jobstatus <job id>"

        job = await get_job(client, settings.aap_api_url, job_id)
        if job is None:
            return "Could not reach AAP"

        return f"Job #{job.id} {job.name}: {job.status}"


def _parse_job_id(raw_text: str) -> int | None:
    parts = raw_text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        return None
    return int(parts[1])
```

Keep formatting helpers (`_format_*`) and argument parsing in the same
file as the command that uses them. If something outside the command needs
the same formatting logic, move it to `formatting.py` (see
`format_count_reply`, used by `!approvals` and `!myjobs`).

`!help` and the unknown-command fallback are both driven by
`commands.list_commands()`, so a new command with a description is
automatically listed in `!help` with no further changes needed.

## 4. Register the command

Add the module to `aap_commands/__init__.py`:

```python
from aap_chatops.aap_commands import approvals, jobstatus, myjobs, ping


def register_aap_commands(client: httpx.AsyncClient, settings: Settings) -> None:
    ping.register(client, settings)
    approvals.register(client, settings)
    myjobs.register(client, settings)
    jobstatus.register(client, settings)
```

## 5. Add command tests

Create `tests/aap_commands/test_<name>.py`. Use the `make_settings`
fixture from `tests/conftest.py` and `httpx.MockTransport` to fake the AAP
response, then assert on the string returned by `dispatch`:

```python
import httpx

from aap_chatops.aap_commands import register_aap_commands
from aap_chatops.commands import CommandContext, dispatch


async def test_jobstatus_command_reports_status(make_settings):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"id": 1, "name": "deploy", "status": "successful"}
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    register_aap_commands(client, make_settings())

    ctx = CommandContext(user_id="U1", channel_id="C1", raw_text="!jobstatus 1")
    assert await dispatch("jobstatus", ctx) == "Job #1 deploy: successful"
```

If the AAP response includes a nested `summary_fields` shape, add a
`make_<name>_payload` factory fixture to `tests/conftest.py` following the
existing pattern, so both the `aap_client` and `aap_commands` tests can
build realistic payloads without duplicating them.

## 6. Verify

```
uv run ruff format src/aap_chatops/aap_commands/<name>.py
uv run ruff check --fix src/aap_chatops/aap_commands/<name>.py
uv run pyright
uv run pytest
```

See `docs/architecture.md` for how dispatch works end to end, and
`docs/testing.md` for test conventions.
