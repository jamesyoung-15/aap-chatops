"""Shared reply-formatting helpers used across multiple AAP commands."""


def format_count_reply(count: int, description: str, lines: list[str]) -> str:
    """Render a "N <description>:\n\n<line>\n<line>..." style reply."""
    header = f"{count} {description}:\n"
    return "\n".join([header, *lines])
