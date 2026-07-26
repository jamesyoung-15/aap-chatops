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
