from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from apscheduler.triggers.cron import CronTrigger

from aap_chatops.alert_config import ScheduledAlert
from aap_chatops.alerts import AlertTaskInfo
from aap_chatops.scheduler import (
    _grace_seconds,
    build_scheduler,
    catch_up,
    most_recent_fire_time,
    run_scheduled_alert,
)
from aap_chatops.state import AlertState

CHICAGO = ZoneInfo("America/Chicago")
WEEKDAYS_AT_TEN = "0 10 * * mon-fri"


@pytest.fixture
def posted():
    """Recording stand-in for the Slack poster."""
    sent: list[tuple[str, str]] = []

    async def post(channel_id: str, text: str) -> None:
        sent.append((channel_id, text))

    post.sent = sent  # pyright: ignore[reportFunctionMemberAccess]
    return post


@pytest.fixture
def state(tmp_path):
    return AlertState.load(tmp_path / "alerts.json")


def make_alert(
    *,
    text: str = "all clear",
    cron: str = WEEKDAYS_AT_TEN,
    catchup: timedelta | None = None,
    fail: bool = False,
    entry_id: str = "digest",
) -> ScheduledAlert:
    async def run() -> str:
        if fail:
            raise RuntimeError("boom")
        return text

    return ScheduledAlert(
        entry_id=entry_id,
        task=AlertTaskInfo(name="digest", description="", run=run),
        trigger=CronTrigger.from_crontab(cron, timezone=CHICAGO),
        channel_id="C0TEST",
        catchup=catchup,
    )


def at(month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, month, day, hour, minute, tzinfo=CHICAGO)


# most_recent_fire_time


def test_most_recent_fire_time_finds_todays_occurrence():
    trigger = CronTrigger.from_crontab(WEEKDAYS_AT_TEN, timezone=CHICAGO)
    # Wednesday 15:30, so 10:00 today has passed.
    found = most_recent_fire_time(trigger, at(7, 29, 15, 30), timedelta(hours=6))
    assert found == at(7, 29, 10, 0)


def test_most_recent_fire_time_returns_none_outside_the_window():
    trigger = CronTrigger.from_crontab(WEEKDAYS_AT_TEN, timezone=CHICAGO)
    found = most_recent_fire_time(trigger, at(7, 29, 15, 30), timedelta(minutes=5))
    assert found is None


def test_most_recent_fire_time_ignores_a_month_old_occurrence():
    """The back from vacation case: a huge gap must not produce a fire time."""
    trigger = CronTrigger.from_crontab(WEEKDAYS_AT_TEN, timezone=CHICAGO)
    assert most_recent_fire_time(trigger, at(8, 28, 9, 0), timedelta(hours=6)) is None


def test_most_recent_fire_time_returns_the_latest_of_several():
    trigger = CronTrigger.from_crontab("0 * * * *", timezone=CHICAGO)
    found = most_recent_fire_time(trigger, at(7, 29, 15, 30), timedelta(hours=5))
    assert found == at(7, 29, 15, 0)


def test_most_recent_fire_time_excludes_future_occurrences():
    trigger = CronTrigger.from_crontab(WEEKDAYS_AT_TEN, timezone=CHICAGO)
    # Wednesday 09:00, before today's 10:00 run.
    found = most_recent_fire_time(trigger, at(7, 29, 9, 0), timedelta(hours=6))
    assert found is None


def test_most_recent_fire_time_includes_an_exact_boundary_hit():
    trigger = CronTrigger.from_crontab(WEEKDAYS_AT_TEN, timezone=CHICAGO)
    found = most_recent_fire_time(trigger, at(7, 29, 10, 0), timedelta(hours=6))
    assert found == at(7, 29, 10, 0)


def test_most_recent_fire_time_skips_the_weekend():
    trigger = CronTrigger.from_crontab(WEEKDAYS_AT_TEN, timezone=CHICAGO)
    # Sunday morning, looking back far enough to reach Friday.
    found = most_recent_fire_time(trigger, at(8, 2, 9, 0), timedelta(days=3))
    assert found == at(7, 31, 10, 0)


def test_most_recent_fire_time_is_dst_correct():
    """10:00 local is a different UTC instant in winter and summer."""
    trigger = CronTrigger.from_crontab(WEEKDAYS_AT_TEN, timezone=CHICAGO)
    winter = most_recent_fire_time(trigger, at(1, 15, 12, 0), timedelta(hours=6))
    summer = most_recent_fire_time(trigger, at(7, 15, 12, 0), timedelta(hours=6))
    assert winter is not None and summer is not None
    assert winter.astimezone(UTC).hour == 16
    assert summer.astimezone(UTC).hour == 15


# run_scheduled_alert


async def test_run_scheduled_alert_posts_and_records(posted, state):
    alert = make_alert(text="2 pending")
    fire_time = at(7, 29, 10)

    await run_scheduled_alert(alert, posted, state, fire_time)

    assert posted.sent == [("C0TEST", "2 pending")]
    assert state.last_fired("digest") == fire_time


async def test_run_scheduled_alert_skips_an_already_handled_occurrence(posted, state):
    alert = make_alert()
    fire_time = at(7, 29, 10)
    state.record("digest", fire_time)

    await run_scheduled_alert(alert, posted, state, fire_time)

    assert posted.sent == []


async def test_run_scheduled_alert_runs_a_newer_occurrence(posted, state):
    alert = make_alert()
    state.record("digest", at(7, 29, 10))

    await run_scheduled_alert(alert, posted, state, at(7, 30, 10))

    assert len(posted.sent) == 1


async def test_run_scheduled_alert_swallows_a_failing_task(posted, state):
    alert = make_alert(fail=True)

    await run_scheduled_alert(alert, posted, state, at(7, 29, 10))

    assert posted.sent == []
    assert state.last_fired("digest") is None


async def test_run_scheduled_alert_swallows_a_failing_post(state):
    async def post(channel_id: str, text: str) -> None:
        raise RuntimeError("slack is down")

    await run_scheduled_alert(make_alert(), post, state, at(7, 29, 10))

    assert state.last_fired("digest") is None


async def test_run_scheduled_alert_does_not_swallow_cancellation(state):
    import asyncio

    async def post(channel_id: str, text: str) -> None:
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await run_scheduled_alert(make_alert(), post, state, at(7, 29, 10))


async def test_a_failed_run_is_retried_on_the_next_attempt(posted, state):
    """State is only recorded on success, so a failure must not mark the run done."""
    fire_time = at(7, 29, 10)
    await run_scheduled_alert(make_alert(fail=True), posted, state, fire_time)
    await run_scheduled_alert(make_alert(), posted, state, fire_time)

    assert len(posted.sent) == 1


# catch_up


async def test_catch_up_skips_alerts_that_did_not_opt_in(posted, state):
    await catch_up([make_alert(catchup=None)], posted, state, at(7, 29, 15, 30))
    assert posted.sent == []


async def test_catch_up_runs_a_recently_missed_occurrence(posted, state):
    alert = make_alert(catchup=timedelta(hours=6))
    await catch_up([alert], posted, state, at(7, 29, 15, 30))
    assert len(posted.sent) == 1
    assert state.last_fired("digest") == at(7, 29, 10)


async def test_catch_up_skips_a_stale_occurrence(posted, state):
    alert = make_alert(catchup=timedelta(minutes=5))
    await catch_up([alert], posted, state, at(7, 29, 15, 30))
    assert posted.sent == []


async def test_catch_up_after_a_month_away_posts_nothing(posted, state):
    alert = make_alert(catchup=timedelta(hours=6))
    await catch_up([alert], posted, state, at(8, 28, 9, 0))
    assert posted.sent == []


async def test_catch_up_posts_at_most_once_per_alert(posted, state):
    """Even a wide window must not replay every occurrence it spans."""
    alert = make_alert(catchup=timedelta(days=30))
    await catch_up([alert], posted, state, at(8, 28, 15, 30))
    assert len(posted.sent) == 1


async def test_catch_up_is_idempotent_across_restarts(posted, state):
    alert = make_alert(catchup=timedelta(hours=6))
    now = at(7, 29, 15, 30)
    await catch_up([alert], posted, state, now)
    await catch_up([alert], posted, state, now)
    assert len(posted.sent) == 1


async def test_catch_up_handles_each_entry_independently(posted, state):
    alerts = [
        make_alert(entry_id="one", catchup=timedelta(hours=6)),
        make_alert(entry_id="two", catchup=timedelta(hours=6)),
    ]
    await catch_up(alerts, posted, state, at(7, 29, 15, 30))
    assert len(posted.sent) == 2


# scheduler wiring


def test_grace_seconds_drops_late_runs_when_catchup_is_off():
    assert _grace_seconds(None) == 1


def test_grace_seconds_matches_the_catchup_window():
    assert _grace_seconds(timedelta(hours=6)) == 21600


def test_build_scheduler_registers_one_job_per_alert(posted, state):
    alerts = [make_alert(entry_id="one"), make_alert(entry_id="two")]
    scheduler = build_scheduler(alerts, posted, state)
    assert {job.id for job in scheduler.get_jobs()} == {"one", "two"}


def test_build_scheduler_applies_catchup_and_coalesce(posted, state):
    alert = make_alert(catchup=timedelta(hours=6))
    job = build_scheduler([alert], posted, state).get_jobs()[0]
    assert job.misfire_grace_time == 21600
    assert job.coalesce is True
    assert job.max_instances == 1
