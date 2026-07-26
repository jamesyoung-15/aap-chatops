import logging

import pytest

from aap_chatops import logging_config
from aap_chatops.logging_config import configure_logging


@pytest.fixture(autouse=True)
def _reset_root_logger():
    """Ensure configure_logging's global root logger changes don't leak between tests."""
    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_level = root_logger.level
    yield
    for handler in list(root_logger.handlers):
        if handler not in original_handlers:
            root_logger.removeHandler(handler)
    root_logger.setLevel(original_level)


def test_configure_logging_sets_level_from_settings(
    tmp_path, monkeypatch, make_settings
):
    monkeypatch.setattr(logging_config, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(
        logging_config, "LOG_FILE", tmp_path / "logs" / "aap_chatops.log"
    )

    configure_logging(make_settings(log_level="DEBUG"))

    assert logging.getLogger().level == logging.DEBUG


def test_configure_logging_creates_log_directory_and_file_handler(
    tmp_path, monkeypatch, make_settings
):
    log_dir = tmp_path / "logs"
    log_file = log_dir / "aap_chatops.log"
    monkeypatch.setattr(logging_config, "LOG_DIR", log_dir)
    monkeypatch.setattr(logging_config, "LOG_FILE", log_file)

    configure_logging(make_settings())

    assert log_dir.is_dir()
    handlers = logging.getLogger().handlers
    added_handlers = [h for h in handlers if getattr(h, "_aap_chatops_handler", False)]
    file_handlers = [h for h in added_handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) == 1
    assert file_handlers[0].baseFilename == str(log_file)


def test_configure_logging_adds_console_handler(tmp_path, monkeypatch, make_settings):
    monkeypatch.setattr(logging_config, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(
        logging_config, "LOG_FILE", tmp_path / "logs" / "aap_chatops.log"
    )

    configure_logging(make_settings())

    handlers = logging.getLogger().handlers
    added_handlers = [h for h in handlers if getattr(h, "_aap_chatops_handler", False)]
    stream_handlers = [
        h
        for h in added_handlers
        if isinstance(h, logging.StreamHandler)
        and not isinstance(h, logging.FileHandler)
    ]
    assert len(stream_handlers) == 1


def test_configure_logging_does_not_duplicate_handlers_on_repeat_calls(
    tmp_path, monkeypatch, make_settings
):
    monkeypatch.setattr(logging_config, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(
        logging_config, "LOG_FILE", tmp_path / "logs" / "aap_chatops.log"
    )

    configure_logging(make_settings())
    handler_count = len(logging.getLogger().handlers)
    configure_logging(make_settings())

    assert len(logging.getLogger().handlers) == handler_count
