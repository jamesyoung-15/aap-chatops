"""Chat-platform-agnostic trigger command registry and dispatch."""

from collections.abc import Callable
from dataclasses import dataclass

CommandHandler = Callable[["CommandContext"], str]

_commands: dict[str, CommandHandler] = {}


@dataclass
class CommandContext:
    """Generic stand-in for a chat platform's incoming message event."""

    user_id: str
    channel_id: str
    raw_text: str


def parse_trigger(text: str) -> str | None:
    """Return the command keyword if `text` is a trigger message, else None."""
    if not text.startswith("!"):
        return None
    parts = text[1:].split(maxsplit=1)
    return parts[0].lower() if parts else None


def command(name: str) -> Callable[[CommandHandler], CommandHandler]:
    """Register `name` (without the leading "!") as a trigger for the decorated handler."""

    def decorator(handler: CommandHandler) -> CommandHandler:
        _commands[name] = handler
        return handler

    return decorator


def dispatch(name: str, ctx: CommandContext) -> str | None:
    """Call the handler registered for `name`, or return None if there isn't one."""
    handler = _commands.get(name)
    if handler is None:
        return None
    return handler(ctx)
