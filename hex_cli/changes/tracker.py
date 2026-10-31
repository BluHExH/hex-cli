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

    def file_paths(self) -> list[str]:
        seen: dict[str, None] = {}
        for r in self.records:
            seen[r.path] = None
        return list(seen.keys())

    def get_latest_for(self, path: str) -> ChangeRecord | None:
        rel = path.replace("\\", "/")
        for r in reversed(self.records):
            if r.path == rel:
                return r
        return None

    def detect_external_modifications(self) -> list[dict[str, Any]]:
        """Compare disk content against last known after-state for each tracked file."""
        external: list[dict[str, Any]] = []
        by_path: dict[str, ChangeRecord] = {}
        for r in self.records:
            by_path[r.path] = r
        for rel, rec in by_path.items():
            target = (self.root / rel).resolve()
            try:
                target.relative_to(self.root)
            except ValueError:
                continue
            if not target.is_file():
                if rec.after is not None:
                    external.append({"path": rel, "reason": "file_missing_on_disk"})
                continue
            try:
                current = target.read_text(encoding="utf-8")
            except OSError as e:
                external.append({"path": rel, "reason": f"read_error: {e}"})
                continue
            expected = rec.after if rec.after is not None else ""
            if current != expected:
                external.append({
                    "path": rel,
                    "reason": "content_diverged",
                    "disk_len": len(current),
                    "expected_len": len(expected),
                })
        return external

    def reject_file(self, path: str) -> dict[str, Any]:
        """Restore a single file to its pre-agent original (if known)."""
        rel = path.replace("\\", "/")
        if rel not in self._originals:
            return {"ok": False, "error": f"No original snapshot for {rel}"}
        original = self._originals[rel]
        target = (self.root / rel).resolve()
        try:
            target.relative_to(self.root)
        except ValueError:
            return {"ok": False, "error": "Path escapes project root"}

        # Refuse if external modification detected
        latest = self.get_latest_for(rel)
        if latest and target.is_file():
            try:
                current = target.read_text(encoding="utf-8")
                if latest.after is not None and current != latest.after:
                    return {
                        "ok": False,
                        "error": "External modification detected; refusing to overwrite",
                        "path": rel,
                    }
            except OSError:
                pass

        try:
            if original is None:
                if target.is_file():
                    target.unlink()
                action = "deleted"
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(original, encoding="utf-8")
                action = "restored"
            # Drop records for this path
            self.records = [r for r in self.records if r.path != rel]
            self._originals.pop(rel, None)
            return {"ok": True, "path": rel, "action": action}
        except OSError as e:
            return {"ok": False, "error": str(e)}

    def accept_file(self, path: str) -> dict[str, Any]:
        """Mark a file's agent changes as accepted (drop from undo pool)."""
        rel = path.replace("\\", "/")
        if rel not in self._originals and not any(r.path == rel for r in self.records):
            return {"ok": False, "error": f"No tracked changes for {rel}"}
        self.records = [r for r in self.records if r.path != rel]
        self._originals.pop(rel, None)
        return {"ok": True, "path": rel, "action": "accepted"}

    def review_summary(self) -> dict[str, Any]:
        """Rich summary for the code-review UI."""
        base = self.summary()
        base["external"] = self.detect_external_modifications()
        base["paths"] = self.file_paths()
        return base
