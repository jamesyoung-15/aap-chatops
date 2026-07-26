# Architecture

## Overview

AAP ChatOps bridges chat platforms (currently Slack) and the Ansible
Automation Platform (AAP) controller API. Chat messages starting with `!`
are parsed into a command keyword, dispatched to a registered handler, and
the handler's reply is posted back to the chat platform.

## Modules

- `commands.py` - platform-agnostic command registry and dispatcher. No
  dependency on Slack or AAP.
- `aap_client.py` - one async function per AAP endpoint used by the bot.
  Each function returns a parsed pydantic model, or `None` on any failure
  (HTTP error, timeout, unexpected response shape). Failures are logged,
  never raised to callers.
- `aap_commands/` - one module per chat command (`ping.py`,
  `approvals.py`, `myjobs.py`), plus `shared.py` for formatting helpers
  used by more than one command. Each module exposes `register(client,
  settings)`; `__init__.py` calls each one from
  `register_aap_commands(client, settings)`.
- `models/` - one file per AAP resource (eg. `workflow_approval.py`), plus
  `base.py` for the generic paginated list envelope.
- `settings.py` - configuration loaded from `.env` via pydantic-settings.
- `logging_config.py` - configures the root logger (file + console).
- `slack_adapter.py` - Slack Socket Mode adapter. The only module aware of
  Slack-specific types.
- `main.py` - composition root: builds settings, configures logging,
  fetches the current AAP user, registers commands, starts the adapter.

## Command dispatch flow

1. `slack_adapter.build_app` registers a listener for any message matching
   `^!`.
2. On a match, `handle_trigger_message(text, user_id, channel_id)` is
   called with the raw Slack message.
3. `commands.parse_trigger(text)` extracts the keyword after `!` (eg.
   `"approvals"`), or returns `None` if the message isn't a trigger.
4. A `CommandContext` is built and passed to `commands.dispatch(keyword,
   ctx)`, which looks up the keyword in the module-level `_commands`
   registry and awaits the handler.
5. The handler (registered by one of the `aap_commands/` modules) calls
   the matching `aap_client` function using the `httpx.AsyncClient` and
   `Settings` it closed over at registration time.
6. `aap_client` issues the HTTP request and parses the JSON response into
   a pydantic model, returning `None` on any failure.
7. The handler formats the result into a plain string reply, handling the
   `None`/empty-result cases with a friendly message.
8. The reply string is returned up through `dispatch`, and
   `on_trigger_message` posts it back to the channel via `say()`. If the
   handler (or `parse_trigger`) returns `None`, no reply is sent.

## Command registration

`commands.py` holds a single module-level registry:

```python
_commands: dict[str, CommandHandler] = {}

def command(name: str):
    def decorator(handler):
        _commands[name] = handler
        return handler
    return decorator
```

`aap_commands/__init__.py` calls each command module's `register(client,
settings)` once at startup:

```python
def register_aap_commands(client, settings):
    ping.register(client, settings)
    approvals.register(client, settings)
    myjobs.register(client, settings)
```

Each command module defines its handler inside its own `register`
function, so the handler closes over the `client`/`settings` passed in at
registration time. This is the project's dependency injection: no
framework, no globals beyond the `commands.py` registry itself. Adding a
new command means adding a new module with a `register` function and one
line in `aap_commands/__init__.py`.

## Models

`models/base.py` defines a generic pagination envelope:

```python
class AapListResponse[T](BaseModel):
    count: int
    next: str | None = None
    previous: str | None = None
    results: list[T]
```

Every AAP list endpoint response is parsed as `AapListResponse[SomeModel]`.
Resource models (eg. `WorkflowApproval`) only include the fields the app
actually uses, not the full AAP schema, and may add small `@property`
helpers (eg. `workflow_name`, `created_by_username`) to safely unwrap
optional nested `summary_fields` without repeating null checks in callers.

## Settings

`Settings` (pydantic-settings `BaseSettings`) loads from `.env`. Two
`model_validator(mode="after")` methods enforce cross-field requirements
that plain field constraints can't express (eg. Slack tokens are only
required when `chat_platform == "slack"`). `aap_api_url` and
`aap_api_headers` are `@computed_field` properties derived from
`aap_base_url`/`aap_api_token`.

`aap_user` is a runtime-only field (`exclude=True`, not sourced from
`.env`): `main.py` fetches the calling AAP user from `/me/` once at
startup and stores it here, so any command handler can filter by "who is
running this" (eg. `!myjobs`) without a repeat lookup.

## Logging

`configure_logging(settings)` configures the root logger with a rotating
file handler (`logs/aap_chatops.log`, 10 MB x 5 backups) and a console
handler, both at `settings.log_level`. Added handlers are tagged with a
custom attribute so repeated calls (eg. across tests) don't attach
duplicates.

## Known gotchas

See `docs/ssl-certificate-verification.md` for why `truststore.inject_into_ssl()`
must run before `slack_bolt` is imported.
