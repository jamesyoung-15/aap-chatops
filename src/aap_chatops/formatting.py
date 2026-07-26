"""Reply-formatting helpers shared by chat commands and scheduled alerts."""

from datetime import UTC, datetime

from aap_chatops.models.base import AapListResponse
from aap_chatops.models.workflow_approval import WorkflowApproval


def format_count_reply(count: int, description: str, lines: list[str]) -> str:
    """Render a "N <description>:\n\n<line>\n<line>..." style reply."""
    header = f"{count} {description}:\n"
    return "\n".join([header, *lines])


def format_expiration(
    expires_at: datetime | None, now: datetime | None = None
) -> str | None:
    """Render an approval's expiration as a human-friendly relative time."""
    if expires_at is None:
        return None

    remaining = expires_at - (now or datetime.now(UTC))
    total_minutes = round(remaining.total_seconds() / 60)
    if total_minutes <= 0:
        return "expired"

    days, hours = divmod(total_minutes // 60, 24)
    minutes = total_minutes % 60
    if days:
        return f"expires in {days}d {hours}h"
    if hours:
        return f"expires in {hours}h {minutes}m"
    return f"expires in {minutes}m"


def format_approval_line(
    approval: WorkflowApproval, now: datetime | None = None
) -> str:
    """Render a single workflow approval as a bulleted Slack message line."""
    workflow = approval.workflow_name or "unknown workflow"
    creator = approval.created_by_username or "unknown user"
    expiration = format_expiration(approval.approval_expiration, now)
    if expiration is None:
        return f"- {workflow} - created by {creator}"
    return f"- {workflow} - created by {creator} - expires: {expiration}"


def format_pending_approvals(
    approvals: AapListResponse[WorkflowApproval], now: datetime | None = None
) -> str:
    """Render pending workflow approvals as a count header plus one line each."""
    lines = [format_approval_line(approval, now) for approval in approvals.results]
    return format_count_reply(approvals.count, "pending workflow approval(s)", lines)
