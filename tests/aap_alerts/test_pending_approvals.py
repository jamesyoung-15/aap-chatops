from pathlib import Path

import httpx

from aap_chatops.aap_alerts import register_aap_alert_tasks
from aap_chatops.alert_config import load_alert_config, resolve_alerts
from aap_chatops.alerts import list_alert_tasks, run_alert_task


def make_client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def approvals_response(*payloads) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "count": len(payloads),
            "next": None,
            "previous": None,
            "results": list(payloads),
        },
    )


async def test_alert_lists_pending_approvals(make_settings, make_approval_payload):
    client = make_client(lambda request: approvals_response(make_approval_payload()))
    register_aap_alert_tasks(client, make_settings())

    message = await run_alert_task("pending_approvals")

    assert message is not None
    assert "1 pending workflow approval(s):" in message
    assert "- (TEST) flow/james_playground" in message
    assert "created by YoungJamesY" in message


async def test_alert_reports_no_pending_approvals(make_settings):
    client = make_client(lambda request: approvals_response())
    register_aap_alert_tasks(client, make_settings())

    assert await run_alert_task("pending_approvals") == "No pending workflow approvals"


async def test_alert_reports_unreachable_aap(make_settings):
    """Unsolicited alerts must say AAP was unreachable, not imply nothing is pending."""
    client = make_client(lambda request: httpx.Response(500))
    register_aap_alert_tasks(client, make_settings())

    assert await run_alert_task("pending_approvals") == "Could not reach AAP"


async def test_alert_queries_only_pending_approvals(
    make_settings, make_approval_payload
):
    seen: list[httpx.URL] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url)
        return approvals_response(make_approval_payload())

    register_aap_alert_tasks(make_client(handler), make_settings())
    await run_alert_task("pending_approvals")

    assert seen[0].params["status"] == "pending"


def test_register_exposes_the_task_with_a_description(make_settings):
    register_aap_alert_tasks(
        make_client(lambda request: approvals_response()), make_settings()
    )

    tasks = list_alert_tasks()
    assert [task.name for task in tasks] == ["pending_approvals"]
    assert tasks[0].description == "Summary of pending workflow approvals"


def test_committed_alerts_yaml_resolves_against_the_registered_tasks(make_settings):
    """Every task named in the repo's alerts.yaml must actually exist once registered."""
    register_aap_alert_tasks(
        make_client(lambda request: approvals_response()), make_settings()
    )

    repo_root = Path(__file__).resolve().parents[2]
    config = load_alert_config(repo_root / "alerts.yaml")
    resolved = resolve_alerts(
        config, default_channel_id="C0TEST", default_timezone="America/Chicago"
    )

    assert [alert.task.name for alert in resolved] == ["pending_approvals"]
