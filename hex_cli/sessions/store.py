"""Versioned on-disk session persistence.

Sessions are stored under ~/.hex/sessions/ as individual JSON files.
No API keys or credentials are ever written into session history.
"""

from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from hex_cli.config import ensure_config_dir, get_config_dir

STORAGE_VERSION = 1


def _sessions_dir() -> Path:
    d = get_config_dir() / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _safe_filename(session_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", session_id)[:64]


@dataclass
class StoredMessage:
    role: str  # user | assistant | tool | system
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None
    timestamp: float = field(default_factory=time.time)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "role": self.role,
            "timestamp": self.timestamp,
        }
        if self.content is not None:
            d["content"] = self.content
        if self.tool_calls is not None:
            d["tool_calls"] = self.tool_calls
        if self.tool_call_id is not None:
            d["tool_call_id"] = self.tool_call_id
        if self.name is not None:
            d["name"] = self.name
        if self.meta:
            d["meta"] = self.meta
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StoredMessage:
        return cls(
            role=data.get("role", "user"),
            content=data.get("content"),
            tool_calls=data.get("tool_calls"),
            tool_call_id=data.get("tool_call_id"),
            name=data.get("name"),
            timestamp=float(data.get("timestamp", time.time())),
            meta=data.get("meta") or {},
        )


@dataclass
class SessionMeta:
    id: str
    name: str
    project_root: str
    provider: str = ""
    model: str = ""
    agent: str = "general"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    message_count: int = 0
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionMeta:
        return cls(
            id=data["id"],
            name=data.get("name", "Session"),
            project_root=data.get("project_root", ""),
            provider=data.get("provider", ""),
            model=data.get("model", ""),
            agent=data.get("agent", "general"),
            created_at=float(data.get("created_at", time.time())),
            updated_at=float(data.get("updated_at", time.time())),
            message_count=int(data.get("message_count", 0)),
            tags=list(data.get("tags") or []),
        )


@dataclass
class StoredSession:
    meta: SessionMeta
    messages: list[StoredMessage] = field(default_factory=list)
    version: int = STORAGE_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "meta": self.meta.to_dict(),
            "messages": [m.to_dict() for m in self.messages],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StoredSession:
        version = int(data.get("version", 1))
        # Future migrations can branch on version here.
        meta = SessionMeta.from_dict(data.get("meta") or {})
        messages = [StoredMessage.from_dict(m) for m in data.get("messages") or []]
        return cls(meta=meta, messages=messages, version=version)


class SessionStore:
    """CRUD + search for durable sessions."""

    def __init__(self, root: Path | None = None):
        self.root = root or _sessions_dir()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        return self.root / f"{_safe_filename(session_id)}.json"

    def create(
        self,
        name: str,
        project_root: str | Path,
        *,
        provider: str = "",
        model: str = "",
        agent: str = "general",
    ) -> StoredSession:
        sid = uuid.uuid4().hex[:12]
        now = time.time()
        meta = SessionMeta(
            id=sid,
            name=name,
            project_root=str(Path(project_root).resolve()),
            provider=provider,
            model=model,
            agent=agent,
            created_at=now,
            updated_at=now,
        )
        session = StoredSession(meta=meta)
        self.save(session)
        return session

    def save(self, session: StoredSession) -> None:
        session.meta.updated_at = time.time()
        session.meta.message_count = len(session.messages)
        path = self._path(session.meta.id)
        # Never persist secrets — strip any accidental key-like fields from meta
        data = session.to_dict()
        if "meta" in data and isinstance(data["meta"], dict):
            for k in list(data["meta"].keys()):
                if "key" in k.lower() or "token" in k.lower() or "secret" in k.lower():
                    data["meta"].pop(k, None)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def load(self, session_id: str) -> StoredSession | None:
        path = self._path(session_id)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return StoredSession.from_dict(data)
        except Exception:
            return None

    def delete(self, session_id: str) -> bool:
        path = self._path(session_id)
        if path.is_file():
            path.unlink()
            return True
        return False

    def rename(self, session_id: str, new_name: str) -> bool:
        session = self.load(session_id)
        if not session:
            return False
        session.meta.name = new_name.strip() or session.meta.name
        self.save(session)
        return True

    def list_sessions(
        self,
        *,
        project_root: str | Path | None = None,
        limit: int = 100,
    ) -> list[SessionMeta]:
        metas: list[SessionMeta] = []
        for path in sorted(self.root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                meta = SessionMeta.from_dict(data.get("meta") or {})
                if project_root is not None:
                    pr = str(Path(project_root).resolve())
                    if meta.project_root != pr:
                        continue
                metas.append(meta)
            except Exception:
                continue
            if len(metas) >= limit:
                break
        return metas

    def search(
        self,
        query: str,
        *,
        project_root: str | Path | None = None,
        limit: int = 30,
    ) -> list[SessionMeta]:
        q = query.strip().lower()
        if not q:
            return self.list_sessions(project_root=project_root, limit=limit)
        results: list[SessionMeta] = []
        for meta in self.list_sessions(project_root=project_root, limit=200):
            hay = f"{meta.name} {meta.agent} {meta.model} {meta.provider}".lower()
            if q in hay:
                results.append(meta)
                if len(results) >= limit:
                    break
                continue
            # Light content search (first few messages only for speed)
            session = self.load(meta.id)
            if session:
                for msg in session.messages[:20]:
                    if msg.content and q in msg.content.lower():
                        results.append(meta)
                        break
                if len(results) >= limit:
                    break
        return results

    def append_message(self, session_id: str, message: StoredMessage) -> bool:
        session = self.load(session_id)
        if not session:
            return False
        session.messages.append(message)
        self.save(session)
        return True

    def replace_messages(self, session_id: str, messages: list[StoredMessage]) -> bool:
        session = self.load(session_id)
        if not session:
            return False
        session.messages = list(messages)
        self.save(session)
        return True
