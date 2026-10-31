"""Project awareness tools — overview, type detection, glob."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hex_cli.config import AppConfig
from hex_cli.permissions import PermissionManager
from hex_cli.tools.filesystem import SKIP_DIRS

# Marker files → project type labels
TYPE_MARKERS: list[tuple[str, str]] = [
    ("pyproject.toml", "python"),
    ("requirements.txt", "python"),
    ("setup.py", "python"),
    ("Pipfile", "python"),
    ("package.json", "nodejs"),
    ("pnpm-lock.yaml", "nodejs"),
    ("yarn.lock", "nodejs"),
    ("Cargo.toml", "rust"),
    ("go.mod", "go"),
    ("pom.xml", "java"),
    ("build.gradle", "java"),
    ("build.gradle.kts", "java"),
    ("composer.json", "php"),
    ("Gemfile", "ruby"),
    ("CMakeLists.txt", "c/c++"),
    ("Makefile", "make"),
]


class ProjectTools:
    def __init__(
        self,
        project_root: Path,
        permissions: PermissionManager,
        config: AppConfig,
    ):
        self.root = project_root.resolve()
        self.perms = permissions
        self.config = config

    def detect_project_type(self) -> dict[str, Any]:
        found: list[str] = []
        markers: list[str] = []
        for filename, label in TYPE_MARKERS:
            p = self.root / filename
            if p.is_file():
                markers.append(filename)
                if label not in found:
                    found.append(label)
        # Fallback heuristics
        if not found:
            if any(self.root.glob("*.py")):
                found.append("python")
            if any(self.root.glob("*.ts")) or any(self.root.glob("*.js")):
                found.append("javascript")
        return {
            "ok": True,
            "types": found or ["unknown"],
            "markers": markers,
            "root": str(self.root),
        }

    def project_overview(self) -> dict[str, Any]:
        type_info = self.detect_project_type()
        top_entries: list[str] = []
        try:
            for p in sorted(self.root.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if p.name in SKIP_DIRS or p.name.startswith("."):
                    if p.name in (".git", ".env", ".gitignore"):
                        top_entries.append(f"{'dir' if p.is_dir() else 'file'}: {p.name}")
                    continue
                kind = "dir" if p.is_dir() else "file"
                top_entries.append(f"{kind}: {p.name}")
                if len(top_entries) >= 40:
                    top_entries.append("…")
                    break
        except OSError as e:
            return {"ok": False, "error": str(e)}

        git = (self.root / ".git").exists()
        return {
            "ok": True,
            "root": str(self.root),
            "types": type_info.get("types", []),
            "markers": type_info.get("markers", []),
            "git": git,
            "top_level": top_entries,
        }

    def glob(
        self,
        pattern: str,
        path: str = ".",
        max_results: int = 100,
    ) -> dict[str, Any]:
        if not pattern or not pattern.strip():
            return {"ok": False, "error": "pattern is required"}
        try:
            base = self.perms.resolve_safe_path(path)
        except PermissionError as e:
            return {"ok": False, "error": str(e)}
        if not base.exists():
            return {"ok": False, "error": f"Path does not exist: {path}"}

        matches: list[str] = []
        try:
            # Path.glob is relative to base
            for p in sorted(base.glob(pattern)):
                if any(part in SKIP_DIRS for part in p.parts):
                    continue
                try:
                    rel = p.relative_to(self.root).as_posix()
                except ValueError:
                    continue
                matches.append(rel)
                if len(matches) >= max_results:
                    break
        except Exception as e:
            return {"ok": False, "error": str(e)}

        return {
            "ok": True,
            "pattern": pattern,
            "matches": matches,
            "count": len(matches),
            "truncated": len(matches) >= max_results,
        }
