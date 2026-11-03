from __future__ import annotations

import json
import re
from typing import Any, Iterator

from hex_cli.providers.base import ChatMessage, ProviderResponse, ToolCall


class MockProvider:
    """Deterministic provider for tests and offline demos."""

    name = "mock"
    model = "mock-smart"

    def __init__(self, model: str = "mock-smart") -> None:
        self.model = model

    def complete(self, messages: list[ChatMessage], tools: list[dict[str, Any]] | None = None) -> ProviderResponse:
        last = next((m.content for m in reversed(messages) if m.role == "user"), "")
        # After tools in the current exchange, summarize (do not re-issue the same tool call)
        if messages and messages[-1].role == "tool":
            tool_bits = [m.content[:500] for m in messages if m.role == "tool"]
            return ProviderResponse(content="Tool results:\n" + "\n".join(tool_bits))
        # Simple scripted tool use
        m = re.search(r"READ\s+(\S+)", last)
        if m and tools:
            return ProviderResponse(
                content="",
                tool_calls=[ToolCall(id="call_1", name="read_file", arguments={"path": m.group(1)})],
            )
        m = re.search(r"WRITE\s+(\S+)\s+::\s+([\s\S]+)", last)
        if m and tools:
            return ProviderResponse(
                content="",
                tool_calls=[
                    ToolCall(
                        id="call_1",
                        name="write_file",
                        arguments={"path": m.group(1), "content": m.group(2)},
                    )
                ],
            )
        if last.startswith("LIST"):
            path = last.split(maxsplit=1)[1] if " " in last else "."
            return ProviderResponse(
                content="",
                tool_calls=[ToolCall(id="call_1", name="list_dir", arguments={"path": path})],
            )
        return ProviderResponse(content=f"HEX mock response: {last[:500]}")

    def stream_text(self, messages: list[ChatMessage]) -> Iterator[str]:
        text = self.complete(messages).content
        for ch in text:
            yield ch
