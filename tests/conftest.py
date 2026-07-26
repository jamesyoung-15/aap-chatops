"""Shared pytest fixtures for the test suite."""

import pytest

from aap_chatops import commands
from aap_chatops.settings import Settings


@pytest.fixture(autouse=True)
def _clear_registry():
    """Ensure the global command registry is empty before and after each test."""
    commands._commands.clear()
    yield
    commands._commands.clear()


@pytest.fixture
def make_settings():
    """Factory fixture for building a Settings instance without reading the local .env."""

    def _make_settings(**overrides) -> Settings:
        fields = {
            "aap_base_url": "aap.example.com",
            "aap_api_token": "test-token",
            "slack_bot_token": "xoxb-test",
            "slack_app_token": "xapp-test",
            **overrides,
        }
        return Settings(_env_file=None, **fields)  # pyright: ignore[reportCallIssue]

    return _make_settings


@pytest.fixture
def make_approval_payload():
    """Factory fixture for building a raw `/workflow_approvals/` result item payload."""

    def _make_approval_payload(**overrides) -> dict:
        payload = {
            "id": 70459,
            "name": "test",
            "status": "pending",
            "created": "2026-07-26T03:52:14.842717Z",
            "approval_expiration": None,
            "can_approve_or_deny": True,
            "timed_out": False,
            "summary_fields": {
                "workflow_job": {"id": 70458, "name": "(TEST) flow/james_playground"},
                "created_by": {"id": 23, "username": "YoungJamesY"},
            },
        }
        payload.update(overrides)
        return payload

    return _make_approval_payload


@pytest.fixture
def make_workflow_job_payload():
    """Factory fixture for building a raw `/workflow_jobs/` result item payload."""

    def _make_workflow_job_payload(**overrides) -> dict:
        payload = {
            "id": 70487,
            "name": "(TEST) flow/james_playground",
            "status": "running",
            "created": "2026-07-26T04:09:27.124567Z",
            "started": "2026-07-26T04:09:27.340787Z",
            "finished": None,
            "elapsed": 5708.179127,
        }
        payload.update(overrides)
        return payload

    return _make_workflow_job_payload


@pytest.fixture
def make_aap_user_payload():
    """Factory fixture for building a raw `/me/` result item payload."""

    def _make_aap_user_payload(**overrides) -> dict:
        payload = {
            "id": 23,
            "username": "YoungJamesY",
            "first_name": "James",
            "last_name": "Young",
            "email": "James.Young@amfam.com",
        }
        payload.update(overrides)
        return payload

    return _make_aap_user_payload
