from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from hex_cli.tools.paths import PathGuard


class FileTools:
    def __init__(self, root: Path) -> None:
        self.guard = PathGuard(root)
        self.root = root.resolve()

    def read_file(self, path: str, max_chars: int = 80_000) -> str:
        p = self.guard.resolve(path)
        if not p.is_file():
            raise FileNotFoundError(path)
        text = p.read_text(encoding="utf-8", errors="replace")
        if len(text) > max_chars:
            return text[:max_chars] + f"\n\n… truncated ({len(text)} chars total)"
        return text

    def write_file(self, path: str, content: str) -> str:
        p = self.guard.resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"wrote {p.relative_to(self.root)} ({len(content)} chars)"

    def list_dir(self, path: str = ".") -> str:
        p = self.guard.resolve(path)
        if not p.is_dir():
            raise NotADirectoryError(path)
        entries = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        lines = []
        for e in entries[:500]:
            kind = "dir" if e.is_dir() else "file"
            lines.append(f"{kind}\t{e.relative_to(self.root)}")
        return "\n".join(lines) or "(empty)"

    def search_files(self, pattern: str, path: str = ".", max_hits: int = 50) -> str:
        base = self.guard.resolve(path)
        rx = re.compile(pattern)
        hits: list[str] = []
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if any(part.startswith(".") for part in p.parts):
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if rx.search(line):
                    hits.append(f"{p.relative_to(self.root)}:{i}:{line[:200]}")
                    if len(hits) >= max_hits:
                        return "\n".join(hits)
        return "\n".join(hits) or "(no matches)"
