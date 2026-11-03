from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from hex_cli.changes.tracker import ChangeLog
from hex_cli.config.settings import HexSettings
from hex_cli.context.compact import compact_messages
from hex_cli.logging_ext import get_logger
from hex_cli.providers.base import ChatMessage, Provider
from hex_cli.tools.registry import ToolRegistry

log = get_logger("agent")


@dataclass
class TurnResult:
    assistant_text: str
    tool_events: list[dict[str, Any]] = field(default_factory=list)
    messages: list[ChatMessage] = field(default_factory=list)


class AgentRunner:
    """Phase-oriented turn runner (Skill SessionRunner concept, native Python)."""

    def __init__(
        self,
        provider: Provider,
        tools: ToolRegistry,
        settings: HexSettings,
        changes: ChangeLog | None = None,
        on_event: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> None:
        self.provider = provider
        self.tools = tools
        self.settings = settings
        self.changes = changes or ChangeLog()
        self.on_event = on_event or (lambda *_: None)

    def _emit(self, phase: str, **payload: Any) -> None:
        self.on_event(phase, payload)

    def run_turn(self, history: list[ChatMessage], user_text: str) -> TurnResult:
        messages = list(history) + [ChatMessage(role="user", content=user_text)]
        messages = compact_messages(messages, self.settings.context_max_chars)
        events: list[dict[str, Any]] = []
        assistant_text = ""

        for round_i in range(self.settings.max_tool_rounds):
            self._emit("model", round=round_i)
            response = self.provider.complete(messages, tools=self.tools.schemas())
            if response.tool_calls:
                if response.content:
                    messages.append(ChatMessage(role="assistant", content=response.content))
                for call in response.tool_calls:
                    self._emit("tool", name=call.name, args=call.arguments)
                    # Track writes
                    before = None
                    if call.name == "write_file":
                        path = str(call.arguments.get("path", ""))
                        target = Path(self.settings.workspace) / path
                        if target.is_file():
                            before = target.read_text(encoding="utf-8", errors="replace")
                    result = self.tools.execute(call.name, call.arguments)
                    if call.name == "write_file" and result.ok:
                        self.changes.record_write(
                            str(call.arguments.get("path", "")),
                            before,
                            str(call.arguments.get("content", "")),
                        )
                    events.append(
                        {
                            "tool": call.name,
                            "ok": result.ok,
                            "output": result.output,
                            "error": result.error,
                        }
                    )
                    messages.append(
                        ChatMessage(
                            role="tool",
                            content=result.output if result.ok else result.error,
                            name=call.name,
                            tool_call_id=call.id,
                        )
                    )
                continue
            assistant_text = response.content
            messages.append(ChatMessage(role="assistant", content=assistant_text))
            self._emit("finalize", text=assistant_text)
            break
        else:
            assistant_text = assistant_text or "Stopped: max tool rounds reached."
            messages.append(ChatMessage(role="assistant", content=assistant_text))

        return TurnResult(assistant_text=assistant_text, tool_events=events, messages=messages)
