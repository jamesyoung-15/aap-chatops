"""Chat-platform-agnostic registry of alert tasks that can be run on a schedule.

A task only knows how to build its message. When it runs, where it posts, and
whether a missed run is worth recovering are all schedule concerns, configured
per entry in `alerts.yaml` rather than baked into the task.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

AlertTask = Callable[[], Awaitable[str]]


@dataclass
class AlertTaskInfo:
    """A registered alert task's function plus metadata for eg. !alerts."""

    name: str
    description: str
    run: AlertTask


_tasks: dict[str, AlertTaskInfo] = {}


def alert_task(name: str, description: str = "") -> Callable[[AlertTask], AlertTask]:
    """Register `name` as a schedulable alert task backed by the decorated function."""

    def decorator(task: AlertTask) -> AlertTask:
        _tasks[name] = AlertTaskInfo(name=name, description=description, run=task)
        return task

    return decorator


def list_alert_tasks() -> list[AlertTaskInfo]:
    """Registered alert tasks, sorted alphabetically by name."""
    return sorted(_tasks.values(), key=lambda info: info.name)


def get_alert_task(name: str) -> AlertTaskInfo | None:
    """The task registered for `name`, or None if nothing is registered under it."""
    return _tasks.get(name)


async def run_alert_task(name: str) -> str | None:
    """Run the task registered for `name`, or return None if there isn't one."""
    info = _tasks.get(name)
    if info is None:
        return None
    return await info.run()
