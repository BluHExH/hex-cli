"""Normalize provider streaming events into a uniform sequence.

Does not simulate streaming by printing finished text character-by-character.
When a provider lacks native streaming, a single final event is emitted.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Iterator


class StreamKind(str, Enum):
    TEXT_DELTA = "text_delta"
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_DELTA = "tool_call_delta"
    TOOL_CALL_END = "tool_call_end"
    FINISH = "finish"
    ERROR = "error"


@dataclass
class StreamEvent:
    kind: StreamKind
    text: str = ""
    tool_call_id: str | None = None
    tool_name: str | None = None
    arguments_delta: str = ""
    finish_reason: str | None = None
    error: str | None = None
    raw: Any = None


@dataclass
class StreamEngine:
    """Collects and normalizes streaming chunks from OpenAI-compatible APIs."""

    on_event: Callable[[StreamEvent], None] | None = None
    _text: str = ""
    _tool_buffers: dict[str, dict[str, Any]] = field(default_factory=dict)
    cancelled: bool = False

    def cancel(self) -> None:
        self.cancelled = True

    def emit(self, event: StreamEvent) -> None:
        if self.cancelled:
            return
        if event.kind == StreamKind.TEXT_DELTA and event.text:
            self._text += event.text
        if self.on_event:
            self.on_event(event)

    def handle_openai_chunk(self, chunk: Any) -> None:
        """Process one OpenAI-style streaming chunk."""
        if self.cancelled:
            return
        try:
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                return
            choice = choices[0]
            delta = getattr(choice, "delta", None)
            finish = getattr(choice, "finish_reason", None)

            if delta is not None:
                content = getattr(delta, "content", None)
                if content:
                    self.emit(StreamEvent(kind=StreamKind.TEXT_DELTA, text=content, raw=chunk))

                tool_calls = getattr(delta, "tool_calls", None) or []
                for tc in tool_calls:
                    idx = str(getattr(tc, "index", 0))
                    buf = self._tool_buffers.setdefault(
                        idx,
                        {"id": "", "name": "", "arguments": ""},
                    )
                    tc_id = getattr(tc, "id", None)
                    if tc_id:
                        buf["id"] = tc_id
                        self.emit(
                            StreamEvent(
                                kind=StreamKind.TOOL_CALL_START,
                                tool_call_id=tc_id,
                                tool_name=getattr(getattr(tc, "function", None), "name", None),
                                raw=chunk,
                            )
                        )
                    fn = getattr(tc, "function", None)
                    if fn is not None:
                        name = getattr(fn, "name", None)
                        if name:
                            buf["name"] = name
                        args = getattr(fn, "arguments", None)
                        if args:
                            buf["arguments"] += args
                            self.emit(
                                StreamEvent(
                                    kind=StreamKind.TOOL_CALL_DELTA,
                                    tool_call_id=buf.get("id") or None,
                                    tool_name=buf.get("name") or None,
                                    arguments_delta=args,
                                    raw=chunk,
                                )
                            )

            if finish:
                for buf in self._tool_buffers.values():
                    if buf.get("id"):
                        self.emit(
                            StreamEvent(
                                kind=StreamKind.TOOL_CALL_END,
                                tool_call_id=buf["id"],
                                tool_name=buf.get("name"),
                                arguments_delta=buf.get("arguments", ""),
                            )
                        )
                self.emit(StreamEvent(kind=StreamKind.FINISH, finish_reason=finish, text=self._text))
        except Exception as exc:
            self.emit(StreamEvent(kind=StreamKind.ERROR, error=str(exc)))

    def finalize_non_streaming(self, content: str | None, tool_calls: list[Any] | None = None) -> None:
        """Emit a single finish event when native streaming is unavailable."""
        if content:
            self.emit(StreamEvent(kind=StreamKind.TEXT_DELTA, text=content))
            self._text = content
        if tool_calls:
            for tc in tool_calls:
                tid = getattr(tc, "id", None) or tc.get("id") if isinstance(tc, dict) else None
                name = getattr(tc, "name", None) or (tc.get("name") if isinstance(tc, dict) else None)
                args = getattr(tc, "arguments", None)
                if isinstance(args, dict):
                    args_s = json.dumps(args)
                else:
                    args_s = str(args or "")
                self.emit(
                    StreamEvent(
                        kind=StreamKind.TOOL_CALL_END,
                        tool_call_id=tid,
                        tool_name=name,
                        arguments_delta=args_s,
                    )
                )
        self.emit(StreamEvent(kind=StreamKind.FINISH, finish_reason="stop", text=self._text))

    @property
    def accumulated_text(self) -> str:
        return self._text
