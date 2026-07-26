from datetime import UTC, datetime, timedelta

from aap_chatops.aap_commands import _format_expiration


def test_format_expiration_returns_none_for_no_timeout():
    assert _format_expiration(None) is None


def test_format_expiration_returns_expired_for_past_time():
    expires_at = datetime.now(UTC) - timedelta(minutes=5)
    assert _format_expiration(expires_at) == "expired"


def test_format_expiration_formats_minutes():
    expires_at = datetime.now(UTC) + timedelta(minutes=30)
    assert _format_expiration(expires_at) == "expires in 30m"


def test_format_expiration_formats_hours_and_minutes():
    expires_at = datetime.now(UTC) + timedelta(hours=2, minutes=15)
    assert _format_expiration(expires_at) == "expires in 2h 15m"


def test_format_expiration_formats_days_and_hours():
    expires_at = datetime.now(UTC) + timedelta(days=1, hours=3)
    assert _format_expiration(expires_at) == "expires in 1d 3h"
