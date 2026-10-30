"""Safe filesystem tools constrained to the project root."""

from __future__ import annotations

import difflib
import re
from pathlib import Path
from typing import Any

from hex_cli.config import AppConfig
from hex_cli.permissions import ActionType, PermissionManager

SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    "dist",
    "build",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "target",
    "vendor",
    ".next",
    "coverage",
    ".idea",
    ".vscode",
}


class FileSystemTools:
    def __init__(
        self,
        project_root: Path,
        permissions: PermissionManager,
        config: AppConfig,
    ):
        self.root = project_root.resolve()
        self.perms = permissions
        self.config = config

    def list_files(self, path: str = ".", recursive: bool = False) -> dict[str, Any]:
        try:
            target = self.perms.resolve_safe_path(path)
        except PermissionError as e:
            return {"ok": False, "error": str(e)}

        if not target.exists():
            return {"ok": False, "error": f"Path does not exist: {path}"}
        if not target.is_dir():
            return {"ok": False, "error": f"Not a directory: {path}"}

        entries: list[str] = []
        if recursive:
            for p in sorted(target.rglob("*")):
                if any(part in SKIP_DIRS for part in p.parts):
                    continue
                try:
                    rel = p.relative_to(self.root).as_posix()
                except ValueError:
                    continue
                kind = "dir" if p.is_dir() else "file"
                entries.append(f"{kind}: {rel}")
                if len(entries) >= 500:
                    entries.append("… (truncated)")
                    break
        else:
            for p in sorted(target.iterdir()):
                if p.name in SKIP_DIRS:
                    continue
                kind = "dir" if p.is_dir() else "file"
                rel = p.relative_to(self.root).as_posix()
                entries.append(f"{kind}: {rel}")

        return {"ok": True, "path": path, "entries": entries, "count": len(entries)}

    def read_file(
        self,
        path: str,
        offset: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        result = self.perms.check(
            ActionType.READ_FILE,
            f"Read file {path}",
            path=path,
        )
        if not result.allowed:
            return {"ok": False, "error": result.reason}

        try:
            target = self.perms.resolve_safe_path(path)
        except PermissionError as e:
            return {"ok": False, "error": str(e)}

        if not target.exists():
            return {"ok": False, "error": f"File not found: {path}"}
        if not target.is_file():
            return {"ok": False, "error": f"Not a file: {path}"}

        size = target.stat().st_size
        if size > self.config.max_file_size_bytes:
            return {
                "ok": False,
                "error": f"File too large ({size} bytes). Limit is {self.config.max_file_size_bytes}.",
            }

        try:
            text = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return {"ok": False, "error": f"Binary or non-UTF-8 file: {path}"}

        lines = text.splitlines(keepends=True)
        total = len(lines)
        start = 0
        if offset is not None and offset > 0:
            start = offset - 1
        end = total
        if limit is not None and limit > 0:
            end = min(start + limit, total)

        sliced = lines[start:end]
        numbered = []
        for i, line in enumerate(sliced, start=start + 1):
            numbered.append(f"{i:6}|{line.rstrip(chr(10) + chr(13))}")

        return {
            "ok": True,
            "path": path,
            "total_lines": total,
            "start_line": start + 1,
            "end_line": start + len(sliced),
            "content": "\n".join(numbered),
        }

    def search_text(
        self,
        pattern: str,
        path: str = ".",
        max_results: int = 30,
    ) -> dict[str, Any]:
        try:
            target = self.perms.resolve_safe_path(path)
        except PermissionError as e:
            return {"ok": False, "error": str(e)}

        try:
            regex = re.compile(pattern)
        except re.error:
            regex = re.compile(re.escape(pattern))

        matches: list[dict[str, Any]] = []
        files_searched = 0

        def _search_file(fp: Path) -> None:
            nonlocal files_searched
            if files_searched > 2000 or len(matches) >= max_results:
                return
            if fp.stat().st_size > self.config.max_file_size_bytes:
                return
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                return
            files_searched += 1
            for i, line in enumerate(text.splitlines(), 1):
                if regex.search(line):
                    rel = fp.relative_to(self.root).as_posix()
                    matches.append({"file": rel, "line": i, "text": line.strip()[:200]})
                    if len(matches) >= max_results:
                        return

        if target.is_file():
            _search_file(target)
        else:
            for p in target.rglob("*"):
                if any(part in SKIP_DIRS for part in p.parts):
                    continue
                if p.is_file():
                    _search_file(p)
                if len(matches) >= max_results:
                    break

        return {
            "ok": True,
            "pattern": pattern,
            "matches": matches,
            "count": len(matches),
            "files_searched": files_searched,
        }

    def write_file(self, path: str, content: str) -> dict[str, Any]:
        try:
            target = self.perms.resolve_safe_path(path)
        except PermissionError as e:
            return {"ok": False, "error": str(e)}

        exists = target.exists()
        action = ActionType.MODIFY_FILE if exists else ActionType.CREATE_FILE
        desc = f"{'Overwrite' if exists else 'Create'} file {path}"

        preview = content if len(content) < 2000 else content[:2000] + "\n… (truncated)"
        result = self.perms.check(
            action,
            desc,
            path=path,
            detail=preview,
        )
        if not result.allowed:
            return {"ok": False, "error": result.reason, "skipped": True}

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if exists and target.is_file():
                backup = target.with_suffix(target.suffix + ".hexbak")
                backup.write_bytes(target.read_bytes())
            target.write_text(content, encoding="utf-8")
        except OSError as e:
            return {"ok": False, "error": f"Write failed: {e}"}

        return {
            "ok": True,
            "path": path,
            "bytes_written": len(content.encode("utf-8")),
            "created": not exists,
        }

    def edit_file(
        self,
        path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> dict[str, Any]:
        try:
            target = self.perms.resolve_safe_path(path)
        except PermissionError as e:
            return {"ok": False, "error": str(e)}

        if not target.exists() or not target.is_file():
            return {"ok": False, "error": f"File not found: {path}"}

        try:
            original = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return {"ok": False, "error": f"Binary or non-UTF-8 file: {path}"}

        count = original.count(old_string)
        if count == 0:
            return {"ok": False, "error": "old_string not found in file"}
        if count > 1 and not replace_all:
            return {
                "ok": False,
                "error": f"old_string found {count} times; set replace_all=true or provide a unique string",
            }

        if replace_all:
            updated = original.replace(old_string, new_string)
        else:
            updated = original.replace(old_string, new_string, 1)

        diff_lines = list(
            difflib.unified_diff(
                original.splitlines(keepends=True),
                updated.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
                n=3,
            )
        )
        diff_text = "".join(diff_lines)
        if len(diff_text) > 3000:
            diff_text = diff_text[:3000] + "\n… (diff truncated)"

        result = self.perms.check(
            ActionType.MODIFY_FILE,
            f"Edit file {path}",
            path=path,
            detail=diff_text,
        )
        if not result.allowed:
            return {"ok": False, "error": result.reason, "skipped": True}

        try:
            backup = target.with_suffix(target.suffix + ".hexbak")
            backup.write_text(original, encoding="utf-8")
            target.write_text(updated, encoding="utf-8")
        except OSError as e:
            return {"ok": False, "error": f"Write failed: {e}"}

        return {
            "ok": True,
            "path": path,
            "replacements": count if replace_all else 1,
            "diff": diff_text,
        }

    def create_directory(self, path: str) -> dict[str, Any]:
        try:
            target = self.perms.resolve_safe_path(path)
        except PermissionError as e:
            return {"ok": False, "error": str(e)}

        if target.exists():
            return {"ok": True, "path": path, "already_exists": True}

        result = self.perms.check(
            ActionType.CREATE_DIRECTORY,
            f"Create directory {path}",
            path=path,
        )
        if not result.allowed:
            return {"ok": False, "error": result.reason, "skipped": True}

        try:
            target.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return {"ok": False, "error": str(e)}

        return {"ok": True, "path": path, "created": True}
