from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Session:
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class SessionStore:
    """JSON session persistence with atomic replace (Skill: keep JSON for HEX)."""

    def __init__(self, workspace: Path) -> None:
        self.root = workspace.resolve() / ".hex" / "sessions"
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        return self.root / f"{session_id}.json"

    def create(self, title: str = "New session") -> Session:
        sid = uuid.uuid4().hex[:12]
        sess = Session(id=sid, title=title, created_at=_now(), updated_at=_now())
        self.save(sess)
        return sess

    def save(self, session: Session) -> None:
        session.updated_at = _now()
        path = self._path(session.id)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(session), indent=2), encoding="utf-8")
        tmp.replace(path)

    def load(self, session_id: str) -> Session:
        data = json.loads(self._path(session_id).read_text(encoding="utf-8"))
        return Session(**data)

    def list(self) -> list[Session]:
        items: list[Session] = []
        for p in sorted(self.root.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                items.append(Session(**data))
            except (json.JSONDecodeError, TypeError, KeyError):
                continue
        return items

    def delete(self, session_id: str) -> None:
        path = self._path(session_id)
        if path.exists():
            path.unlink()
