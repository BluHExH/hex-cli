from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator, Protocol


@dataclass
class ChatMessage:
    role: str
    content: str
    tool_call_id: str | None = None
    name: str | None = None


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ProviderResponse:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Any = None


class Provider(Protocol):
    name: str
    model: str

    def complete(self, messages: list[ChatMessage], tools: list[dict[str, Any]] | None = None) -> ProviderResponse:
        ...

    def stream_text(self, messages: list[ChatMessage]) -> Iterator[str]:
        ...
