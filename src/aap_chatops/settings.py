"""Project configurable settings loaded from .env"""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """User configurations for project such as API tokens"""

    chat_platform: Literal["slack", "teams"] = Field(
        default="slack", description="Which chat application to use."
    )

    # aap configs
    aap_base_url: str | None = Field(
        default=None, description="AAP hostname (eg. <aap-domain>.com)"
    )
    aap_api_token: str | None = Field(default=None, description="AAP API token")

    # slack configs
    slack_bot_token: str | None = Field(
        default=None, description="Slack bot token to interact with Slack workspace"
    )
    slack_app_token: str | None = Field(
        default=None,
        description="Slack account token used to authenticate socket mode connections",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


if __name__ == "__main__":
    print(Settings().model_dump())
