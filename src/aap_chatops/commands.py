"""Chat-platform-agnostic trigger command registry and dispatch."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

CommandHandler = Callable[["CommandContext"], Awaitable[str]]


@dataclass
class CommandContext:
    """Generic stand-in for a chat platform's incoming message event."""

    user_id: str
    channel_id: str
    raw_text: str


@dataclass
class CommandInfo:
    """A registered command's handler plus metadata for eg. !help."""

    name: str
    description: str
    handler: CommandHandler


_commands: dict[str, CommandInfo] = {}


def parse_trigger(text: str) -> str | None:
    """Return the command keyword if `text` is a trigger message, else None."""
    if not text.startswith("!"):
        return None
    parts = text[1:].split(maxsplit=1)
    return parts[0].lower() if parts else None


def command(
    name: str, description: str = ""
) -> Callable[[CommandHandler], CommandHandler]:
    """Register `name` (without the leading "!") as a trigger for the decorated handler."""

    def decorator(handler: CommandHandler) -> CommandHandler:
        _commands[name] = CommandInfo(
            name=name, description=description, handler=handler
        )
        return handler

    return decorator


def list_commands() -> list[CommandInfo]:
    """Registered commands, sorted alphabetically by name."""
    return sorted(_commands.values(), key=lambda info: info.name)


async def dispatch(name: str, ctx: CommandContext) -> str:
    """Call the handler registered for `name`, or return a fallback message if unknown."""
    info = _commands.get(name)
    if info is None:
        return f"Unknown command: !{name}. Try !help for a list of commands."
    return await info.handler(ctx)
