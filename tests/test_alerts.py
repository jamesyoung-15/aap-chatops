from aap_chatops import alerts


async def test_run_alert_task_calls_registered_task():
    @alerts.alert_task("digest")
    async def build_digest() -> str:
        return "all clear"

    assert await alerts.run_alert_task("digest") == "all clear"


async def test_run_alert_task_returns_none_for_unknown_task():
    assert await alerts.run_alert_task("nope") is None


def test_get_alert_task_returns_none_for_unknown_task():
    assert alerts.get_alert_task("nope") is None


def test_alert_task_decorator_returns_the_original_function():
    async def build_digest() -> str:
        return "all clear"

    decorated = alerts.alert_task("digest")(build_digest)
    assert decorated is build_digest


def test_list_alert_tasks_returns_sorted_by_name():
    @alerts.alert_task("zeta")
    async def build_zeta() -> str:
        return "z"

    @alerts.alert_task("alpha")
    async def build_alpha() -> str:
        return "a"

    assert [info.name for info in alerts.list_alert_tasks()] == ["alpha", "zeta"]


def test_list_alert_tasks_includes_description():
    @alerts.alert_task("alpha", description="First task")
    async def build_alpha() -> str:
        return "a"

    assert alerts.list_alert_tasks()[0].description == "First task"


def test_list_alert_tasks_is_empty_by_default():
    assert alerts.list_alert_tasks() == []


async def test_registering_the_same_name_twice_replaces_the_task():
    @alerts.alert_task("digest")
    async def build_first() -> str:
        return "first"

    @alerts.alert_task("digest")
    async def build_second() -> str:
        return "second"

    assert len(alerts.list_alert_tasks()) == 1
    assert await alerts.run_alert_task("digest") == "second"
