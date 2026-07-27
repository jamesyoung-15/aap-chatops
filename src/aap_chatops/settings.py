"""Project configurable settings loaded from .env"""

from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from aap_chatops.models.aap_user import AAPUser


class Settings(BaseSettings):
    """User configurations for project such as API tokens"""

    chat_platform: Literal["slack", "teams"] = Field(
        default="slack", description="Which chat application to use."
    )

    # aap configs (required)
    aap_base_url: str = Field(
        default="", description="AAP hostname (eg. <aap-domain>.com)"
    )
    aap_api_token: str = Field(default="", description="AAP API token")

    # slack configs (only required if user set to slack)
    slack_bot_token: str | None = Field(
        default=None, description="Slack bot token to interact with Slack workspace"
    )
    slack_app_token: str | None = Field(
        default=None,
        description="Slack account token used to authenticate socket mode connections",
    )

    # scheduled alert configs
    alerts_enabled: bool = Field(
        default=True,
        description="Run scheduled alerts alongside the chat listener. Set false on any "
        "second instance, or two bots will post the same alert to the same channel.",
    )
    alerts_config_path: Path = Field(
        default=Path("alerts.yaml"), description="Path to the alert schedule config"
    )
    default_alert_channel_id: str | None = Field(
        default=None,
        description="Channel id alerts post to when an entry doesn't name one "
        "(eg. C0123456789)",
    )
    alert_timezone: str = Field(
        default="America/Chicago",
        description="IANA timezone alert schedules are interpreted in",
    )

    # Runtime-only cache, not sourced from env; populated once at startup and
    # reused by commands that need to know who's calling (eg. !myjobs).
    aap_user: AAPUser | None = Field(default=None, exclude=True)

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging verbosity"
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @model_validator(mode="after")
    def _require_platform_tokens(self) -> "Settings":
        """Fail fast if the tokens for the selected chat_platform aren't configured."""
        if self.chat_platform == "slack" and not (
            self.slack_bot_token and self.slack_app_token
        ):
            raise ValueError(
                "slack_bot_token and slack_app_token are required when chat_platform is 'slack'"
            )
        return self

    @field_validator("alert_timezone")
    @classmethod
    def _validate_alert_timezone(cls, value: str) -> str:
        """Catch a typo at startup rather than when an alert first tries to fire."""
        try:
            ZoneInfo(value)
        except (ValueError, KeyError) as exc:
            raise ValueError(f"unknown timezone {value!r}") from exc
        return value

    @model_validator(mode="after")
    def _require_aap_configurations(self) -> "Settings":
        if not self.aap_api_token or not self.aap_base_url:
            raise ValueError("aap_base_url and aap_api_token are required")
        return self

    @computed_field
    @property
    def aap_api_url(self) -> str:
        """Construct the AAP API URL from the base URL"""
        return f"https://{self.aap_base_url}/api/controller/v2"

    @computed_field
    @property
    def aap_api_headers(self) -> dict[str, str]:
        """Construct the headers for AAP API requests"""
        return {"Authorization": f"Bearer {self.aap_api_token}"}


if __name__ == "__main__":
    print(Settings().model_dump())
