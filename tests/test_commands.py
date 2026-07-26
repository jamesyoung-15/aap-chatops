from aap_chatops import commands
from aap_chatops.commands import CommandContext, parse_trigger


def test_parse_trigger_returns_keyword():
    assert parse_trigger("!approvals") == "approvals"


def test_parse_trigger_is_case_insensitive():
    assert parse_trigger("!Approvals") == "approvals"


def test_parse_trigger_ignores_extra_words():
    assert parse_trigger("!approvals please") == "approvals"


def test_parse_trigger_returns_none_for_non_trigger_text():
    assert parse_trigger("hello there") is None


def test_parse_trigger_returns_none_for_bare_bang():
    assert parse_trigger("!") is None


async def test_dispatch_calls_registered_handler():
    @commands.command("ping")
    async def handle_ping(ctx: CommandContext) -> str:
        return f"pong to {ctx.user_id}"

    ctx = CommandContext(user_id="U1", channel_id="C1", raw_text="!ping")
    assert await commands.dispatch("ping", ctx) == "pong to U1"


async def test_dispatch_returns_fallback_message_for_unknown_command():
    ctx = CommandContext(user_id="U1", channel_id="C1", raw_text="!nope")
    reply = await commands.dispatch("nope", ctx)
    assert reply == "Unknown command: !nope. Try !help for a list of commands."


def test_list_commands_returns_sorted_by_name():
    @commands.command("zeta")
    async def handle_zeta(ctx: CommandContext) -> str:
        return "z"

    @commands.command("alpha", description="First command")
    async def handle_alpha(ctx: CommandContext) -> str:
        return "a"

    names = [info.name for info in commands.list_commands()]
    assert names == ["alpha", "zeta"]


def test_list_commands_includes_description():
    @commands.command("alpha", description="First command")
    async def handle_alpha(ctx: CommandContext) -> str:
        return "a"

    infos = commands.list_commands()
    assert infos[0].description == "First command"
