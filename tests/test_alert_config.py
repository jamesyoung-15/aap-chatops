from datetime import timedelta
from pathlib import Path
from textwrap import dedent

import pytest

from aap_chatops import alerts
from aap_chatops.alert_config import (
    AlertConfig,
    AlertConfigError,
    load_alert_config,
    resolve_alerts,
)

CHANNEL = "C0DEFAULT"
TIMEZONE = "America/Chicago"


@pytest.fixture
def registered_task():
    """Register a single 'digest' alert task for resolve_alerts to bind against."""

    @alerts.alert_task("digest", description="Test digest")
    async def build_digest() -> str:
        return "all clear"

    return alerts.get_alert_task("digest")


def write_config(tmp_path, body: str):
    path = tmp_path / "alerts.yaml"
    path.write_text(dedent(body), encoding="utf-8")
    return path


def resolve(config: AlertConfig, **overrides):
    kwargs = {"default_channel_id": CHANNEL, "default_timezone": TIMEZONE, **overrides}
    return resolve_alerts(config, **kwargs)


def make_config(**overrides) -> AlertConfig:
    entry = {"task": "digest", "cron": "0 10 * * 1-5", **overrides}
    return AlertConfig.model_validate({"alerts": [entry]})


def test_load_alert_config_parses_a_valid_file(tmp_path):
    path = write_config(
        tmp_path,
        """
        alerts:
          - task: digest
            cron: "0 10 * * 1-5"
            catchup_minutes: 360
        """,
    )
    config = load_alert_config(path)
    assert len(config.alerts) == 1
    assert config.alerts[0].task == "digest"
    assert config.alerts[0].catchup_minutes == 360
    assert config.alerts[0].enabled is True


def test_load_alert_config_treats_an_empty_file_as_no_alerts(tmp_path):
    assert load_alert_config(write_config(tmp_path, "")).alerts == []


def test_load_alert_config_raises_for_a_missing_file(tmp_path):
    with pytest.raises(AlertConfigError, match="Could not read"):
        load_alert_config(tmp_path / "nope.yaml")


def test_load_alert_config_raises_for_malformed_yaml(tmp_path):
    with pytest.raises(AlertConfigError, match="Could not parse"):
        load_alert_config(write_config(tmp_path, "alerts: [unclosed"))


def test_load_alert_config_raises_for_a_non_mapping_document(tmp_path):
    with pytest.raises(AlertConfigError, match="must be a mapping"):
        load_alert_config(write_config(tmp_path, "- just\n- a list\n"))


def test_load_alert_config_raises_for_an_unknown_key(tmp_path):
    path = write_config(
        tmp_path,
        """
        alerts:
          - task: digest
            cron: "0 10 * * 1-5"
            catchup_mintues: 360
        """,
    )
    with pytest.raises(AlertConfigError, match="catchup_mintues"):
        load_alert_config(path)


def test_load_alert_config_raises_for_a_bad_cron_expression(tmp_path):
    path = write_config(
        tmp_path,
        """
        alerts:
          - task: digest
            cron: "not a cron"
        """,
    )
    with pytest.raises(AlertConfigError, match="invalid cron expression"):
        load_alert_config(path)


def test_load_alert_config_raises_for_an_unknown_timezone(tmp_path):
    path = write_config(
        tmp_path,
        """
        alerts:
          - task: digest
            cron: "0 10 * * 1-5"
            timezone: America/Chicaco
        """,
    )
    with pytest.raises(AlertConfigError, match="unknown timezone"):
        load_alert_config(path)


def test_load_alert_config_raises_for_a_non_positive_catchup(tmp_path):
    path = write_config(
        tmp_path,
        """
        alerts:
          - task: digest
            cron: "0 10 * * 1-5"
            catchup_minutes: 0
        """,
    )
    with pytest.raises(AlertConfigError, match="catchup_minutes"):
        load_alert_config(path)


def test_resolve_alerts_binds_the_registered_task(registered_task):
    resolved = resolve(make_config(catchup_minutes=360))
    assert len(resolved) == 1
    assert resolved[0].task is registered_task
    assert resolved[0].channel_id == CHANNEL
    assert resolved[0].catchup == timedelta(hours=6)


def test_resolve_alerts_defaults_catchup_to_none(registered_task):
    assert resolve(make_config())[0].catchup is None


def test_resolve_alerts_uses_the_entry_channel_over_the_default(registered_task):
    resolved = resolve(make_config(channel="C0OVERRIDE"))
    assert resolved[0].channel_id == "C0OVERRIDE"


def test_resolve_alerts_raises_for_an_unknown_task(registered_task):
    config = AlertConfig.model_validate(
        {"alerts": [{"task": "nope", "cron": "0 10 * * 1-5"}]}
    )
    with pytest.raises(AlertConfigError, match="Unknown alert task 'nope'"):
        resolve(config)


def test_unknown_task_error_lists_registered_tasks(registered_task):
    config = AlertConfig.model_validate(
        {"alerts": [{"task": "nope", "cron": "0 10 * * 1-5"}]}
    )
    with pytest.raises(AlertConfigError, match="Registered tasks: digest"):
        resolve(config)


def test_resolve_alerts_raises_when_no_channel_is_resolvable(registered_task):
    with pytest.raises(AlertConfigError, match="has no channel"):
        resolve(make_config(), default_channel_id=None)


def test_resolve_alerts_skips_disabled_entries(registered_task):
    assert resolve(make_config(enabled=False)) == []


def test_resolve_alerts_raises_for_duplicate_entries(registered_task):
    entry = {"task": "digest", "cron": "0 10 * * 1-5"}
    config = AlertConfig.model_validate({"alerts": [entry, dict(entry)]})
    with pytest.raises(AlertConfigError, match="Duplicate alert entry"):
        resolve(config)


def test_resolve_alerts_allows_one_task_on_several_schedules(registered_task):
    config = AlertConfig.model_validate(
        {
            "alerts": [
                {"task": "digest", "cron": "0 10 * * 1-5"},
                {"task": "digest", "cron": "0 16 * * 1-5"},
            ]
        }
    )
    resolved = resolve(config)
    assert len({alert.entry_id for alert in resolved}) == 2


def test_resolve_alerts_allows_one_task_on_several_channels(registered_task):
    """Same task and cron to two channels is legitimate, so the id must include the channel."""
    config = AlertConfig.model_validate(
        {
            "alerts": [
                {"task": "digest", "cron": "0 10 * * 1-5", "channel": "C0ONE"},
                {"task": "digest", "cron": "0 10 * * 1-5", "channel": "C0TWO"},
            ]
        }
    )
    resolved = resolve(config)
    assert len({alert.entry_id for alert in resolved}) == 2


def test_resolve_alerts_returns_empty_for_no_entries():
    assert resolve(AlertConfig()) == []


def test_resolve_alerts_applies_the_default_timezone(registered_task):
    resolved = resolve(make_config())
    assert str(resolved[0].trigger.timezone) == TIMEZONE


def test_resolve_alerts_applies_a_per_entry_timezone(registered_task):
    resolved = resolve(make_config(timezone="UTC"))
    assert str(resolved[0].trigger.timezone) == "UTC"


def test_committed_alerts_yaml_is_valid():
    """The repo's own alerts.yaml must always parse, even before its tasks exist."""
    repo_root = Path(__file__).resolve().parents[1]
    assert load_alert_config(repo_root / "alerts.yaml").alerts
