from hex_cli.context.compact import compact_messages
from hex_cli.providers.base import ChatMessage


def test_compact_trims():
    msgs = [ChatMessage("user", "x" * 100) for _ in range(20)]
    out = compact_messages(msgs, max_chars=250)
    assert sum(len(m.content) for m in out) <= 250 + 50  # note message slack
