from datetime import UTC, datetime, timedelta

from aap_chatops.formatting import (
    format_approval_line,
    format_count_reply,
    format_expiration,
    format_pending_approvals,
)
from aap_chatops.models.base import AapListResponse
from aap_chatops.models.workflow_approval import WorkflowApproval

NOW = datetime(2026, 7, 26, 12, 0, tzinfo=UTC)


def test_format_count_reply_joins_header_and_lines():
    reply = format_count_reply(2, "pending workflow approval(s)", ["- a", "- b"])
    assert reply == "2 pending workflow approval(s):\n\n- a\n- b"


def test_format_count_reply_with_no_lines():
    reply = format_count_reply(0, "workflow job(s) run today", [])
    assert reply == "0 workflow job(s) run today:\n"


def test_format_expiration_returns_none_for_no_timeout():
    assert format_expiration(None) is None


def test_format_expiration_returns_expired_for_past_time():
    assert format_expiration(NOW - timedelta(minutes=5), NOW) == "expired"


def test_format_expiration_formats_minutes():
    assert format_expiration(NOW + timedelta(minutes=30), NOW) == "expires in 30m"


def test_format_expiration_formats_hours_and_minutes():
    expires_at = NOW + timedelta(hours=2, minutes=15)
    assert format_expiration(expires_at, NOW) == "expires in 2h 15m"


def test_format_expiration_formats_days_and_hours():
    expires_at = NOW + timedelta(days=1, hours=3)
    assert format_expiration(expires_at, NOW) == "expires in 1d 3h"


def test_format_expiration_defaults_to_current_time():
    assert format_expiration(datetime.now(UTC) - timedelta(minutes=5)) == "expired"


def test_format_approval_line_without_expiration(make_approval_payload):
    approval = WorkflowApproval.model_validate(make_approval_payload())
    line = format_approval_line(approval, NOW)
    assert line == "- (TEST) flow/james_playground - created by YoungJamesY"


def test_format_approval_line_with_expiration(make_approval_payload):
    payload = make_approval_payload(
        approval_expiration=(NOW + timedelta(hours=3)).isoformat()
    )
    approval = WorkflowApproval.model_validate(payload)
    line = format_approval_line(approval, NOW)
    assert line.endswith(" - expires: expires in 3h 0m")


def test_format_approval_line_falls_back_to_unknown_fields(make_approval_payload):
    payload = make_approval_payload()
    payload["summary_fields"] = {}
    approval = WorkflowApproval.model_validate(payload)
    line = format_approval_line(approval, NOW)
    assert line == "- unknown workflow - created by unknown user"


def test_format_pending_approvals_renders_count_and_lines(make_approval_payload):
    approvals = AapListResponse[WorkflowApproval].model_validate(
        {"count": 1, "results": [make_approval_payload()]}
    )
    reply = format_pending_approvals(approvals, NOW)
    assert reply == (
        "1 pending workflow approval(s):\n"
        "\n"
        "- (TEST) flow/james_playground - created by YoungJamesY"
    )


def test_format_pending_approvals_uses_count_not_page_length(make_approval_payload):
    """AAP `count` is the total, which can exceed the results on this page."""
    approvals = AapListResponse[WorkflowApproval].model_validate(
        {"count": 25, "results": [make_approval_payload()]}
    )
    assert format_pending_approvals(approvals, NOW).startswith(
        "25 pending workflow approval(s):"
    )
