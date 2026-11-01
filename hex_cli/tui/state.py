"""Shared session state for the HEX TUI."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hex_cli.sessions.store import (
    SessionStore,
    StoredMessage,
    StoredSession,
    SessionMeta,
)


@dataclass
class ChatEntry:
    """One row in the conversation panel."""

    kind: str  # user | assistant | tool | system | error | status
    text: str
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """One conversation session (in-memory + optional durable id)."""

    id: str
    name: str
    entries: list[ChatEntry] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    agent: str = "general"
    provider: str = ""
    model: str = ""
    persistent_id: str | None = None  # id in SessionStore when saved

    @staticmethod
    def create(name: str | None = None, index: int = 1, agent: str = "general") -> Session:
        sid = uuid.uuid4().hex[:10]
        return Session(id=sid, name=name or f"Session {index}", agent=agent)


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
    agent: str = "general"
    _session_counter: int = 0
    _store: SessionStore | None = None

    def __post_init__(self) -> None:
        self._store = SessionStore()
        if not self.sessions:
            self._session_counter = 1
            s = Session.create(index=1, agent=self.agent)
            s.provider = self.provider_name
            s.model = self.model
            self.sessions.append(s)
            self.active_session_id = s.id

    @property
    def store(self) -> SessionStore:
        if self._store is None:
            self._store = SessionStore()
        return self._store

    @property
    def active_session(self) -> Session:
        for s in self.sessions:
            if s.id == self.active_session_id:
                return s
        if self.sessions:
            self.active_session_id = self.sessions[0].id
            return self.sessions[0]
        self._session_counter += 1
        s = Session.create(index=self._session_counter, agent=self.agent)
        self.sessions.append(s)
        self.active_session_id = s.id
        return s

    @property
    def entries(self) -> list[ChatEntry]:
        return self.active_session.entries

    def add(self, kind: str, text: str, **meta: Any) -> ChatEntry:
        entry = ChatEntry(kind=kind, text=text, meta=meta)
        self.active_session.entries.append(entry)
        # Auto-title from first user message if still default name
        s = self.active_session
        if kind == "user" and s.name.startswith("Session "):
            title = (text or "").strip().splitlines()[0][:48]
            if title:
                s.name = title
        # Best-effort auto-persist (ignore failures)
        try:
            self.persist_active()
        except Exception:
            pass
        return entry

    def clear_conversation(self) -> None:
        self.active_session.entries.clear()
        self.status_message = "Conversation cleared"

    def new_session(self, name: str | None = None, agent: str | None = None) -> Session:
        self._session_counter += 1
        s = Session.create(
            name=name,
            index=self._session_counter,
            agent=agent or self.agent,
        )
        s.provider = self.provider_name
        s.model = self.model
        self.sessions.append(s)
        self.active_session_id = s.id
        self.status_message = f"New session: {s.name}"
        return s

    def switch_session(self, session_id: str) -> bool:
        for s in self.sessions:
            if s.id == session_id:
                self.active_session_id = session_id
                self.agent = s.agent
                return True
        return False

    def rename_session(self, session_id: str, new_name: str) -> bool:
        for s in self.sessions:
            if s.id == session_id:
                s.name = new_name.strip() or s.name
                if s.persistent_id:
                    self.store.rename(s.persistent_id, s.name)
                return True
        return False

    def delete_session(self, session_id: str) -> bool:
        for i, s in enumerate(self.sessions):
            if s.id == session_id:
                if s.persistent_id:
                    self.store.delete(s.persistent_id)
                self.sessions.pop(i)
                if not self.sessions:
                    self.new_session()
                elif self.active_session_id == session_id:
                    self.active_session_id = self.sessions[0].id
                return True
        return False

    def session_names(self) -> list[tuple[str, str, bool]]:
        """Return (id, name, is_active) for sidebar."""
        return [
            (s.id, s.name, s.id == self.active_session_id) for s in self.sessions
        ]

    def persist_active(self) -> str | None:
        """Save active session to disk; return persistent id."""
        s = self.active_session
        messages = [
            StoredMessage(
                role=e.kind if e.kind in ("user", "assistant", "tool", "system") else "system",
                content=e.text,
                meta=dict(e.meta) if e.meta else {},
            )
            for e in s.entries
            if e.kind in ("user", "assistant", "tool", "system")
        ]
        if s.persistent_id:
            stored = self.store.load(s.persistent_id)
            if stored:
                stored.messages = messages
                stored.meta.name = s.name
                stored.meta.agent = s.agent
                stored.meta.provider = self.provider_name
                stored.meta.model = self.model
                self.store.save(stored)
                return s.persistent_id
        stored = self.store.create(
            s.name,
            self.project_root,
            provider=self.provider_name,
            model=self.model,
            agent=s.agent,
        )
        stored.messages = messages
        self.store.save(stored)
        s.persistent_id = stored.meta.id
        return s.persistent_id

    def load_persistent(self, persistent_id: str) -> bool:
        """Load a disk session into memory and activate it."""
        stored = self.store.load(persistent_id)
        if not stored:
            return False
        s = Session(
            id=uuid.uuid4().hex[:10],
            name=stored.meta.name,
            agent=stored.meta.agent or "general",
            provider=stored.meta.provider,
            model=stored.meta.model,
            persistent_id=stored.meta.id,
            created_at=stored.meta.created_at,
        )
        for m in stored.messages:
            s.entries.append(
                ChatEntry(
                    kind=m.role,
                    text=m.content or "",
                    meta=dict(m.meta) if m.meta else {},
                )
            )
        self.sessions.append(s)
        self.active_session_id = s.id
        self.agent = s.agent
        return True

    def list_persistent(self) -> list[SessionMeta]:
        return self.store.list_sessions(project_root=self.project_root)

    def search_persistent(self, query: str) -> list[SessionMeta]:
        return self.store.search(query, project_root=self.project_root)
