import pytest
from pydantic import ValidationError


def test_settings_succeeds_with_full_config(make_settings):
    settings = make_settings()
    assert settings.aap_api_url == "https://aap.example.com/api/controller/v2"
    assert settings.aap_api_headers == {"Authorization": "Bearer test-token"}


def test_settings_requires_aap_base_url(make_settings):
    with pytest.raises(ValidationError):
        make_settings(aap_base_url="")


def test_settings_requires_aap_api_token(make_settings):
    with pytest.raises(ValidationError):
        make_settings(aap_api_token="")


def test_settings_requires_slack_tokens_when_chat_platform_is_slack(make_settings):
    with pytest.raises(ValidationError):
        make_settings(slack_bot_token=None, slack_app_token=None)


def test_settings_does_not_require_slack_tokens_when_chat_platform_is_teams(
    make_settings,
):
    settings = make_settings(
        chat_platform="teams", slack_bot_token=None, slack_app_token=None
    )
    assert settings.slack_bot_token is None


def test_settings_defaults_alerts_on_with_no_channel(make_settings):
    """An alert channel is only required by entries that don't name one."""
    settings = make_settings()
    assert settings.alerts_enabled is True
    assert settings.default_alert_channel_id is None


def test_settings_rejects_an_unknown_alert_timezone(make_settings):
    with pytest.raises(ValidationError, match="unknown timezone"):
        make_settings(alert_timezone="America/Chicaco")


def test_settings_accepts_a_valid_alert_timezone(make_settings):
    assert make_settings(alert_timezone="UTC").alert_timezone == "UTC"
