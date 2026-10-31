"""Shared session state for the HEX TUI."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ChatEntry:
    """One row in the conversation panel."""

    kind: str
    text: str
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """One conversation session."""

    id: str
    name: str
    entries: list[ChatEntry] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    @staticmethod
    def create(name: str | None = None, index: int = 1) -> Session:
        sid = uuid.uuid4().hex[:10]
        return Session(id=sid, name=name or f"Session {index}")


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
    sessions: list[Session] = field(default_factory=list)
    active_session_id: str = ""
    token_hint: str = "—"
    _session_counter: int = 0

    def __post_init__(self) -> None:
        if not self.sessions:
            self._session_counter = 1
            s = Session.create(index=1)
            self.sessions.append(s)
            self.active_session_id = s.id

    @property
    def active_session(self) -> Session:
        for s in self.sessions:
            if s.id == self.active_session_id:
                return s
        if self.sessions:
            self.active_session_id = self.sessions[0].id
            return self.sessions[0]
        self._session_counter += 1
        s = Session.create(index=self._session_counter)
        self.sessions.append(s)
        self.active_session_id = s.id
        return s

    @property
    def entries(self) -> list[ChatEntry]:
        return self.active_session.entries

    def add(self, kind: str, text: str, **meta: Any) -> ChatEntry:
        entry = ChatEntry(kind=kind, text=text, meta=meta)
        self.active_session.entries.append(entry)
        return entry

    def clear_conversation(self) -> None:
        self.active_session.entries.clear()
        self.status_message = "Conversation cleared"

    def new_session(self, name: str | None = None) -> Session:
        self._session_counter += 1
        s = Session.create(name=name, index=self._session_counter)
        self.sessions.append(s)
        self.active_session_id = s.id
        self.status_message = f"New session: {s.name}"
        return s

    def switch_session(self, session_id: str) -> bool:
        for s in self.sessions:
            if s.id == session_id:
                self.active_session_id = session_id
                return True
        return False

    def session_names(self) -> list[tuple[str, str, bool]]:
        return [
            (s.id, s.name, s.id == self.active_session_id) for s in self.sessions
        ]
