"""Track agent file mutations for review, diff, and undo."""

from __future__ import annotations

import difflib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ChangeRecord:
    path: str
    action: str  # create | modify | delete
    before: str | None
    after: str | None
    timestamp: float = field(default_factory=time.time)

    def unified_diff(self, context: int = 3) -> str:
        before_lines = (self.before or "").splitlines(keepends=True)
        after_lines = (self.after or "").splitlines(keepends=True)
        diff = difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile=f"a/{self.path}",
            tofile=f"b/{self.path}",
            n=context,
        )
        return "".join(diff)

    def stats(self) -> tuple[int, int]:
        """Return (added, removed) line counts."""
        before_lines = (self.before or "").splitlines()
        after_lines = (self.after or "").splitlines()
        matcher = difflib.SequenceMatcher(None, before_lines, after_lines)
        added = removed = 0
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "insert":
                added += j2 - j1
            elif tag == "delete":
                removed += i2 - i1
            elif tag == "replace":
                removed += i2 - i1
                added += j2 - j1
        return added, removed


class ChangeTracker:
    """In-session change log for agent-driven file edits."""

    def __init__(self, project_root: Path):
        self.root = project_root.resolve()
        self.records: list[ChangeRecord] = []
        # Snapshots for undo: path -> original content before first agent touch
        self._originals: dict[str, str | None] = {}

    def record(
        self,
        path: str,
        action: str,
        before: str | None,
        after: str | None,
    ) -> ChangeRecord:
        rel = path.replace("\\", "/")
        if rel not in self._originals:
            self._originals[rel] = before
        rec = ChangeRecord(path=rel, action=action, before=before, after=after)
        self.records.append(rec)
        return rec

    def summary(self) -> dict[str, Any]:
        by_path: dict[str, ChangeRecord] = {}
        for r in self.records:
            by_path[r.path] = r  # last wins
        files = []
        total_add = total_rem = 0
        for path, r in sorted(by_path.items()):
            add, rem = r.stats()
            total_add += add
            total_rem += rem
            files.append(
                {
                    "path": path,
                    "action": r.action,
                    "added": add,
                    "removed": rem,
                }
            )
        return {
            "files": files,
            "file_count": len(files),
            "added": total_add,
            "removed": total_rem,
            "change_events": len(self.records),
        }

    def all_diffs(self) -> str:
        by_path: dict[str, ChangeRecord] = {}
        for r in self.records:
            by_path[r.path] = r
        parts = []
        for path in sorted(by_path):
            d = by_path[path].unified_diff()
            if d:
                parts.append(d)
        return "\n".join(parts) if parts else "(no textual diffs)"

    def undo_last(self) -> dict[str, Any]:
        """Restore the most recent change event (best-effort)."""
        if not self.records:
            return {"ok": False, "error": "No changes to undo"}
        rec = self.records.pop()
        target = (self.root / rec.path).resolve()
        try:
            target.relative_to(self.root)
        except ValueError:
            return {"ok": False, "error": "Path escapes project root"}

        try:
            if rec.action == "create":
                if target.is_file():
                    target.unlink()
                return {"ok": True, "restored": rec.path, "action": "deleted_created_file"}
            if rec.before is None:
                return {"ok": False, "error": "No before-content to restore"}
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(rec.before, encoding="utf-8")
            return {"ok": True, "restored": rec.path, "action": "restored_content"}
        except OSError as e:
            return {"ok": False, "error": str(e)}

    def undo_all_originals(self) -> dict[str, Any]:
        """Restore every file to content before first agent touch in this session."""
        restored = []
        errors = []
        for rel, original in list(self._originals.items()):
            target = (self.root / rel).resolve()
            try:
                target.relative_to(self.root)
            except ValueError:
                errors.append(f"{rel}: path escape")
                continue
            try:
                if original is None:
                    if target.is_file():
                        target.unlink()
                        restored.append(rel)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(original, encoding="utf-8")
                    restored.append(rel)
            except OSError as e:
                errors.append(f"{rel}: {e}")
        self.records.clear()
        self._originals.clear()
        return {"ok": not errors, "restored": restored, "errors": errors}

    def clear(self) -> None:
        self.records.clear()
        self._originals.clear()
