"""Project configurable settings loaded from .env"""

from typing import Literal

from pydantic import Field, computed_field, model_validator
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
