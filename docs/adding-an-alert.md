# Adding a new alert

Steps to add a scheduled alert. An alert has two halves: a *task* in code
that builds the message, and an *entry* in `alerts.yaml` that says when and
where to post it. One task can have several entries.

## 1. Add a model and client function (if the endpoint is new)

Same as for a command, see steps 1 and 2 of `adding-a-command.md`. Skip
this if `aap_client.py` already covers the endpoint.

## 2. Add a task module

Create `src/aap_chatops/aap_alerts/<name>.py`. Like command modules, it
exposes `register(client, settings)` and defines the task inside it, so the
task closes over the client and settings:

```python
def register(client: httpx.AsyncClient, settings: Settings) -> None:
    @alert_task("failed_jobs", description="Workflow jobs that failed today")
    async def failed_jobs() -> str:
        jobs = await get_failed_workflow_jobs(client, settings.aap_api_url)
        if jobs is None:
            return "Could not reach AAP"
        if not jobs.results:
            return "No failed workflow jobs today"
        return format_count_reply(jobs.count, "failed workflow job(s)", [...])
```

The task returns a string and knows nothing about schedules or channels.
It always returns something: alerts are unsolicited, so "Could not reach
AAP" is reported rather than passed over in silence, which would read as
"nothing to report".

Reuse rendering helpers from `formatting.py` rather than writing new ones.

## 3. Register it

Add one line to `aap_alerts/__init__.py`, the same way
`aap_commands/__init__.py` works.

## 4. Add a schedule entry

Add an entry to your `alerts.yaml`. See `alerts.example.yaml` for the
available fields.

Two things that bite:

- The day of week must be `*` or names (`mon-fri`, `tue,thu`). Numbers are
  rejected, because APScheduler counts 0 as Monday rather than Sunday, so
  `1-5` would mean tue-sat.
- Leaving out `catchup_minutes` means a run missed while the bot was down
  is dropped. Set it only where a late post is still worth having.

An unknown task name fails at startup with the list of registered tasks, so
a typo here will not wait until the alert was due to fire.

## 5. Add tests

Create `tests/aap_alerts/test_<name>.py`, following
`tests/aap_alerts/test_pending_approvals.py`: `httpx.MockTransport` for the
AAP response, `register(...)`, then assert on `run_alert_task("<name>")`.
Cover the success, empty, and unreachable cases.

## 6. Verify

```bash
uv run ruff format src/aap_chatops/aap_alerts/<name>.py
uv run ruff check --fix src/aap_chatops/aap_alerts/<name>.py
uv run pyright src/
uv run pytest
```

To see it fire without waiting, temporarily set the entry's cron to
`* * * * *` and run the bot. Delete `.state/alerts.json` if you need it to
post the same occurrence again.

See `docs/architecture.md` for how the alert flow works end to end, and
`docs/testing.md` for test conventions.
