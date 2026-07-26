import httpx

from aap_chatops.aap_commands import register_aap_commands
from aap_chatops.commands import CommandContext, dispatch
from aap_chatops.models.aap_user import AAPUser


async def test_myjobs_command_lists_jobs_run_today(
    make_settings, make_workflow_job_payload
):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [make_workflow_job_payload()],
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    settings = make_settings()
    settings.aap_user = AAPUser(id=23, username="YoungJamesY")
    register_aap_commands(client, settings)

    ctx = CommandContext(user_id="U1", channel_id="C1", raw_text="!myjobs")
    reply = await dispatch("myjobs", ctx)

    assert reply is not None
    assert "1 workflow job(s) run today:" in reply
    assert "#70487 (TEST) flow/james_playground - running" in reply
    assert "https://aap.example.com/jobs/workflow/70487/output" in reply


async def test_myjobs_command_reports_no_jobs_today(make_settings):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"count": 0, "next": None, "previous": None, "results": []}
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    settings = make_settings()
    settings.aap_user = AAPUser(id=23, username="YoungJamesY")
    register_aap_commands(client, settings)

    ctx = CommandContext(user_id="U1", channel_id="C1", raw_text="!myjobs")
    assert await dispatch("myjobs", ctx) == "No workflow jobs run today"


async def test_myjobs_command_reports_unreachable_aap(make_settings):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    settings = make_settings()
    settings.aap_user = AAPUser(id=23, username="YoungJamesY")
    register_aap_commands(client, settings)

    ctx = CommandContext(user_id="U1", channel_id="C1", raw_text="!myjobs")
    assert await dispatch("myjobs", ctx) == "Could not reach AAP"


async def test_myjobs_command_reports_unknown_user_when_aap_user_missing(
    make_settings,
):
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("should not call AAP when aap_user is unset")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    settings = make_settings()
    assert settings.aap_user is None
    register_aap_commands(client, settings)

    ctx = CommandContext(user_id="U1", channel_id="C1", raw_text="!myjobs")
    assert await dispatch("myjobs", ctx) == "Could not determine your AAP user"
