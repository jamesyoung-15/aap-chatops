"""Durable record of which scheduled alert occurrences have already been handled.

Keyed by entry id and storing the *scheduled* occurrence rather than the wall clock
time it ran, so a late catch-up run can still tell whether that occurrence was
already posted. Without this, a restart would re-post whatever it caught up on.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_STATE_FILE = Path(".state/alerts.json")


@dataclass
class AlertState:
    """Last scheduled occurrence successfully posted, per alert entry."""

    path: Path
    _fired: dict[str, datetime] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "AlertState":
        """Read state from `path`, falling back to empty state if it is missing or unusable."""
        return cls(path=path, _fired=_read(path))

    def last_fired(self, entry_id: str) -> datetime | None:
        """The most recent occurrence posted for `entry_id`, if any."""
        return self._fired.get(entry_id)

    def record(self, entry_id: str, fire_time: datetime) -> None:
        """Mark `fire_time` as handled for `entry_id` and persist."""
        self._fired[entry_id] = fire_time
        self._write()

    def _write(self) -> None:
        payload = {
            entry_id: fired.isoformat()
            for entry_id, fired in sorted(self._fired.items())
        }
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # Write via a temp file so a crash mid-write cannot truncate existing state.
            tmp = self.path.with_suffix(f"{self.path.suffix}.tmp")
            tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            os.replace(tmp, self.path)
        except OSError:
            logger.exception("Could not write alert state to %s", self.path)


def _read(path: Path) -> dict[str, datetime]:
    """Parse the state file. Never raises: bad state must not stop the bot."""
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except OSError:
        logger.exception("Could not read alert state from %s", path)
        return {}

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Alert state at %s is not valid JSON, starting empty", path)
        return {}

    if not isinstance(parsed, dict):
        logger.warning("Alert state at %s is not an object, starting empty", path)
        return {}

    return {
        entry_id: fired
        for entry_id, value in parsed.items()
        if (fired := _parse_fired(entry_id, value)) is not None
    }


def _parse_fired(entry_id: str, value: object) -> datetime | None:
    """Drop unparseable or naive entries rather than discarding the whole file."""
    if not isinstance(value, str):
        logger.warning("Ignoring non-string alert state for %r", entry_id)
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        logger.warning("Ignoring unparseable alert state %r for %r", value, entry_id)
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
