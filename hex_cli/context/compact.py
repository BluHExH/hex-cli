from __future__ import annotations

from hex_cli.providers.base import ChatMessage


def compact_messages(messages: list[ChatMessage], max_chars: int) -> list[ChatMessage]:
    """Simple budget trim — PARTIAL vs OpenCode SessionCompaction."""
    total = sum(len(m.content) for m in messages)
    if total <= max_chars:
        return messages
    # Keep system-ish first message and recent tail
    if not messages:
        return messages
    head = messages[:1]
    tail = messages[1:]
    kept: list[ChatMessage] = []
    budget = max_chars - sum(len(m.content) for m in head)
    for m in reversed(tail):
        if budget <= 0:
            break
        if len(m.content) <= budget:
            kept.append(m)
            budget -= len(m.content)
    kept.reverse()
    note = ChatMessage(role="system", content="[context trimmed to fit budget]")
    return head + [note] + kept
