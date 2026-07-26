import pytest
from pydantic import ValidationError

from aap_chatops.settings import Settings


def _make_settings(**overrides) -> Settings:
    fields = {
        "aap_base_url": "aap.example.com",
        "aap_api_token": "test-token",
        "slack_bot_token": "xoxb-test",
        "slack_app_token": "xapp-test",
        **overrides,
    }
    # _env_file=None to avoid using local .env
    return Settings(_env_file=None, **fields)  # pyright: ignore[reportCallIssue]


def test_settings_succeeds_with_full_config():
    settings = _make_settings()
    assert settings.aap_api_url == "https://aap.example.com/api/controller/v2"
    assert settings.aap_api_headers == {"Authorization": "Bearer test-token"}


def test_settings_requires_aap_base_url():
    with pytest.raises(ValidationError):
        _make_settings(aap_base_url="")


def test_settings_requires_aap_api_token():
    with pytest.raises(ValidationError):
        _make_settings(aap_api_token="")


def test_settings_requires_slack_tokens_when_chat_platform_is_slack():
    with pytest.raises(ValidationError):
        _make_settings(slack_bot_token=None, slack_app_token=None)


def test_settings_does_not_require_slack_tokens_when_chat_platform_is_teams():
    settings = _make_settings(
        chat_platform="teams", slack_bot_token=None, slack_app_token=None
    )
    assert settings.slack_bot_token is None
