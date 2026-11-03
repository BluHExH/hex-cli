from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FileChange:
    path: str
    before: str | None
    after: str | None


@dataclass
class ChangeLog:
    """In-memory change journal with restore (snapshot-inspired, not OpenCode copy)."""

    items: list[FileChange] = field(default_factory=list)

    def record_write(self, path: str, before: str | None, after: str) -> None:
        self.items.append(FileChange(path=path, before=before, after=after))

    def restore_last(self, root: Path) -> FileChange | None:
        if not self.items:
            return None
        change = self.items.pop()
        target = (root / change.path).resolve()
        if change.before is None:
            if target.exists():
                target.unlink()
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(change.before, encoding="utf-8")
        return change
