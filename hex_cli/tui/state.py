"""Shared session state for the HEX TUI."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ChatEntry:
    """One row in the conversation panel."""

    kind: str  # user | assistant | tool | system | error | status
    text: str
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionState:
    """Mutable UI + agent session state."""

    project_root: Path
    provider_name: str
    model: str
    connected: bool = False
    status_message: str = "Ready"
    sidebar_visible: bool = True
    busy: bool = False
    entries: list[ChatEntry] = field(default_factory=list)
    sessions: list[str] = field(default_factory=lambda: ["Session 1"])
    active_session: int = 0
    token_hint: str = "—"

    def add(self, kind: str, text: str, **meta: Any) -> ChatEntry:
        entry = ChatEntry(kind=kind, text=text, meta=meta)
        self.entries.append(entry)
        return entry

    def clear_conversation(self) -> None:
        self.entries.clear()
        self.status_message = "Conversation cleared"
