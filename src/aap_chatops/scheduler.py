"""Runs scheduled alerts alongside the chat listener.

Every alert run is funnelled through `run_scheduled_alert`, which never raises. The
scheduler shares an event loop and a TaskGroup with the chat adapter, so an alert
that escaped would take the listener down with it.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from aap_chatops.alert_config import ScheduledAlert
from aap_chatops.state import DEFAULT_STATE_FILE, AlertState

logger = logging.getLogger(__name__)

MessagePoster = Callable[[str, str], Awaitable[None]]

ALERT_TIMEOUT_SECONDS = 60.0

# Guards a frequent cron paired with a long catch-up window from scanning forever.
MAX_CATCHUP_STEPS = 10_000

# How far back a firing job looks to identify which occurrence it is running for.
# Only needs to cover scheduler lateness, not downtime.
OCCURRENCE_LOOKBACK = timedelta(hours=1)


def most_recent_fire_time(
    trigger: CronTrigger, now: datetime, within: timedelta
) -> datetime | None:
    """Latest fire time in (now - within, now], or None if it did not fire in that window.

    APScheduler 3.x has no `get_previous_fire_time`, so walk forward from the edge of
    the window. Bounding the search by `within` is what makes a stale occurrence
    unreachable rather than found and then rejected.
    """
    candidate = trigger.get_next_fire_time(None, now - within)
    latest = None
    for _ in range(MAX_CATCHUP_STEPS):
        if candidate is None or candidate > now:
            return latest
        latest = candidate
        candidate = trigger.get_next_fire_time(candidate, candidate)

    logger.warning(
        "Gave up scanning for the last fire time after %s steps; "
        "the cron is too frequent for this catch-up window",
        MAX_CATCHUP_STEPS,
    )
    return None


async def run_scheduled_alert(
    alert: ScheduledAlert,
    post: MessagePoster,
    state: AlertState,
    fire_time: datetime,
) -> None:
    """Run one alert and post its message. Never raises."""
    last = state.last_fired(alert.entry_id)
    if last is not None and last >= fire_time:
        logger.debug(
            "Alert %r already handled its %s run", alert.entry_id, fire_time.isoformat()
        )
        return

    try:
        async with asyncio.timeout(ALERT_TIMEOUT_SECONDS):
            text = await alert.task.run()
            await post(alert.channel_id, text)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("Alert %r failed", alert.entry_id)
        return

    state.record(alert.entry_id, fire_time)
    logger.info("Alert %r posted its %s run", alert.entry_id, fire_time.isoformat())


async def run_due_alert(
    alert: ScheduledAlert, post: MessagePoster, state: AlertState
) -> None:
    """APScheduler job body: work out which occurrence this run is for, then run it."""
    now = _utc_now()
    lookback = max(alert.catchup or OCCURRENCE_LOOKBACK, OCCURRENCE_LOOKBACK)
    fire_time = most_recent_fire_time(alert.trigger, now, lookback) or now
    await run_scheduled_alert(alert, post, state, fire_time)


async def catch_up(
    alerts: list[ScheduledAlert], post: MessagePoster, state: AlertState, now: datetime
) -> None:
    """Re-run the most recent missed occurrence of each alert that opted into catch-up."""
    for alert in alerts:
        if alert.catchup is None:
            continue

        fire_time = most_recent_fire_time(alert.trigger, now, alert.catchup)
        if fire_time is None:
            logger.info(
                "Alert %r had no occurrence in the last %s, nothing to catch up",
                alert.entry_id,
                alert.catchup,
            )
            continue

        await run_scheduled_alert(alert, post, state, fire_time)


def build_scheduler(
    alerts: list[ScheduledAlert], post: MessagePoster, state: AlertState
) -> AsyncIOScheduler:
    """Register every alert on its trigger. The caller starts the returned scheduler."""
    scheduler = AsyncIOScheduler()
    for alert in alerts:
        scheduler.add_job(
            run_due_alert,
            trigger=alert.trigger,
            args=[alert, post, state],
            id=alert.entry_id,
            name=alert.task.name,
            misfire_grace_time=_grace_seconds(alert.catchup),
            # Collapse a burst of missed runs into one, eg. after a long suspend.
            coalesce=True,
            max_instances=1,
        )
    return scheduler


async def run_alerts(
    alerts: list[ScheduledAlert],
    post: MessagePoster,
    *,
    state_path: Path | None = None,
) -> None:
    """Catch up on missed runs, then serve the schedule until cancelled."""
    state = AlertState.load(state_path or DEFAULT_STATE_FILE)
    await catch_up(alerts, post, state, _utc_now())

    scheduler = build_scheduler(alerts, post, state)
    scheduler.start()
    for job in scheduler.get_jobs():
        logger.info("Alert %r next runs at %s", job.id, job.next_run_time)

    try:
        await asyncio.Event().wait()
    finally:
        scheduler.shutdown(wait=False)


def _grace_seconds(catchup: timedelta | None) -> int:
    """A late fire is only worth running if the entry opted into catch-up."""
    return 1 if catchup is None else int(catchup.total_seconds())


def _utc_now() -> datetime:
    return datetime.now(UTC)
