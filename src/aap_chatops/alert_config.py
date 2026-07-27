"""Parsing and validation of `alerts.yaml`, the schedule definitions for alert tasks.

Config is bound to the task registry at startup by `resolve_alerts`, so a typo in
a task name, cron expression, or timezone fails the process at boot rather than
going unnoticed until the alert was supposed to fire.
"""

import logging
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from apscheduler.triggers.cron import CronTrigger
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from aap_chatops.alerts import AlertTaskInfo, get_alert_task, list_alert_tasks

logger = logging.getLogger(__name__)


class AlertConfigError(ValueError):
    """Raised when `alerts.yaml` is unreadable, malformed, or references something unknown."""


class AlertEntry(BaseModel):
    """One scheduled run of an alert task, as written in `alerts.yaml`."""

    task: str
    cron: str
    timezone: str | None = None
    channel: str | None = None
    catchup_minutes: int | None = Field(default=None, gt=0)
    enabled: bool = True

    # Reject unknown keys so a misspelled field is an error rather than a silent no-op.
    model_config = ConfigDict(extra="forbid")

    @field_validator("cron")
    @classmethod
    def _validate_cron(cls, value: str) -> str:
        """Let APScheduler parse the expression, but reject its day of week footgun first."""
        fields = value.split()
        if len(fields) != 5:
            raise ValueError(
                f"invalid cron expression {value!r}: expected 5 fields, got {len(fields)}"
            )
        # APScheduler numbers days from 0=Monday while cron uses 0=Sunday, and
        # from_crontab does not translate, so "1-5" silently means tue-sat. Names are
        # unambiguous, and from_crontab rejects misspelled ones on its own.
        if any(char.isdigit() for char in fields[4]):
            raise ValueError(
                f"invalid cron expression {value!r}: the day of week field must be '*' or "
                "day names such as 'mon-fri'. Numbers are rejected because APScheduler "
                "counts 0 as Monday, so '1-5' would mean tue-sat rather than mon-fri."
            )
        try:
            CronTrigger.from_crontab(value)
        except ValueError as exc:
            raise ValueError(f"invalid cron expression {value!r}: {exc}") from exc
        return value

    @field_validator("timezone")
    @classmethod
    def _validate_timezone(cls, value: str | None) -> str | None:
        if value is not None:
            _build_zone(value)
        return value


class AlertConfig(BaseModel):
    """Top level shape of `alerts.yaml`."""

    alerts: list[AlertEntry] = []

    model_config = ConfigDict(extra="forbid")


@dataclass(frozen=True)
class ScheduledAlert:
    """A config entry bound to its registered task, ready to hand to the scheduler."""

    entry_id: str
    task: AlertTaskInfo
    trigger: CronTrigger
    channel_id: str
    catchup: timedelta | None


def load_alert_config(path: Path) -> AlertConfig:
    """Read and validate `alerts.yaml`. Raises AlertConfigError on any problem."""
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise AlertConfigError(
            f"No alert config at {path}. Copy alerts.example.yaml to alerts.yaml, "
            "or set alerts_enabled=false to run without scheduled alerts."
        ) from exc
    except OSError as exc:
        raise AlertConfigError(f"Could not read alert config {path}: {exc}") from exc

    try:
        parsed = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise AlertConfigError(f"Could not parse alert config {path}: {exc}") from exc

    if parsed is None:
        return AlertConfig()
    if not isinstance(parsed, dict):
        raise AlertConfigError(
            f"Alert config {path} must be a mapping, got {type(parsed).__name__}"
        )

    try:
        return AlertConfig.model_validate(parsed)
    except ValidationError as exc:
        raise AlertConfigError(f"Invalid alert config {path}:\n{exc}") from exc


def resolve_alerts(
    config: AlertConfig,
    *,
    default_channel_id: str | None,
    default_timezone: str,
) -> list[ScheduledAlert]:
    """Bind each enabled entry to its registered task. Raises AlertConfigError on a mismatch."""
    resolved: list[ScheduledAlert] = []
    seen: set[str] = set()

    for entry in config.alerts:
        if not entry.enabled:
            logger.info("Alert entry for task %r is disabled, skipping", entry.task)
            continue

        task = get_alert_task(entry.task)
        if task is None:
            raise AlertConfigError(
                f"Unknown alert task {entry.task!r}. "
                f"Registered tasks: {_registered_task_names() or 'none'}"
            )

        channel_id = entry.channel or default_channel_id
        if not channel_id:
            raise AlertConfigError(
                f"Alert task {entry.task!r} has no channel: set 'channel' on the entry "
                "or configure default_alert_channel_id"
            )

        trigger = CronTrigger.from_crontab(
            entry.cron, timezone=_build_zone(entry.timezone or default_timezone)
        )

        entry_id = f"{entry.task}@{entry.cron}#{channel_id}"
        if entry_id in seen:
            raise AlertConfigError(f"Duplicate alert entry {entry_id!r}")
        seen.add(entry_id)

        resolved.append(
            ScheduledAlert(
                entry_id=entry_id,
                task=task,
                trigger=trigger,
                channel_id=channel_id,
                catchup=_build_catchup(entry.catchup_minutes),
            )
        )

    _log_unscheduled_tasks(resolved)
    return resolved


def _build_zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except (ValueError, KeyError) as exc:
        raise ValueError(f"unknown timezone {name!r}") from exc


def _build_catchup(minutes: int | None) -> timedelta | None:
    return None if minutes is None else timedelta(minutes=minutes)


def _registered_task_names() -> str:
    return ", ".join(info.name for info in list_alert_tasks())


def _log_unscheduled_tasks(resolved: list[ScheduledAlert]) -> None:
    """Surface registered tasks nothing schedules, so 'why isn't it firing' is answerable."""
    scheduled = {alert.task.name for alert in resolved}
    for info in list_alert_tasks():
        if info.name not in scheduled:
            logger.info("Alert task %r is registered but not scheduled", info.name)
