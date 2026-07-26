from datetime import UTC, datetime

from aap_chatops.state import AlertState

FIRED = datetime(2026, 7, 29, 15, 0, tzinfo=UTC)


def test_load_returns_empty_state_for_a_missing_file(tmp_path):
    state = AlertState.load(tmp_path / "alerts.json")
    assert state.last_fired("anything") is None


def test_record_then_reload_round_trips(tmp_path):
    path = tmp_path / "alerts.json"
    AlertState.load(path).record("digest@cron", FIRED)
    assert AlertState.load(path).last_fired("digest@cron") == FIRED


def test_record_creates_the_parent_directory(tmp_path):
    path = tmp_path / "nested" / "dir" / "alerts.json"
    AlertState.load(path).record("digest", FIRED)
    assert path.exists()


def test_record_keeps_existing_entries(tmp_path):
    path = tmp_path / "alerts.json"
    state = AlertState.load(path)
    state.record("first", FIRED)
    state.record("second", FIRED)
    reloaded = AlertState.load(path)
    assert reloaded.last_fired("first") == FIRED
    assert reloaded.last_fired("second") == FIRED


def test_record_leaves_no_temp_file_behind(tmp_path):
    path = tmp_path / "alerts.json"
    AlertState.load(path).record("digest", FIRED)
    assert [p.name for p in tmp_path.iterdir()] == ["alerts.json"]


def test_load_ignores_invalid_json(tmp_path):
    path = tmp_path / "alerts.json"
    path.write_text("{not json", encoding="utf-8")
    assert AlertState.load(path).last_fired("digest") is None


def test_load_ignores_a_non_object_document(tmp_path):
    path = tmp_path / "alerts.json"
    path.write_text('["a", "b"]', encoding="utf-8")
    assert AlertState.load(path).last_fired("digest") is None


def test_load_drops_only_the_unparseable_entries(tmp_path):
    path = tmp_path / "alerts.json"
    path.write_text(
        '{"good": "2026-07-29T15:00:00+00:00", "bad": "not a date", "wrong": 5}',
        encoding="utf-8",
    )
    state = AlertState.load(path)
    assert state.last_fired("good") == FIRED
    assert state.last_fired("bad") is None
    assert state.last_fired("wrong") is None


def test_load_treats_a_naive_timestamp_as_utc(tmp_path):
    path = tmp_path / "alerts.json"
    path.write_text('{"digest": "2026-07-29T15:00:00"}', encoding="utf-8")
    assert AlertState.load(path).last_fired("digest") == FIRED
