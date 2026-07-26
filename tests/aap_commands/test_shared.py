from aap_chatops.aap_commands.shared import format_count_reply


def test_format_count_reply_joins_header_and_lines():
    reply = format_count_reply(2, "pending workflow approval(s)", ["- a", "- b"])
    assert reply == "2 pending workflow approval(s):\n\n- a\n- b"


def test_format_count_reply_with_no_lines():
    reply = format_count_reply(0, "workflow job(s) run today", [])
    assert reply == "0 workflow job(s) run today:\n"
