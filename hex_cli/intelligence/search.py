"""Ignore-aware project text search with context lines."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

DEFAULT_IGNORE_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", "node_modules", ".venv", "venv",
    "dist", "build", ".tox", ".mypy_cache", ".pytest_cache", ".hex",
}


@dataclass
class SearchHit:
    path: str
    line: int
    text: str
    context_before: list[str]
    context_after: list[str]


def _should_skip(path: Path) -> bool:
    return any(part in DEFAULT_IGNORE_DIRS or part.startswith(".") for part in path.parts)


def project_search(
    root: Path,
    pattern: str,
    *,
    path: str = ".",
    max_results: int = 40,
    context: int = 1,
    regex: bool = False,
) -> list[SearchHit]:
    """Search project files; returns structured hits with context."""
    root = root.resolve()
    base = (root / path).resolve()
    if not str(base).startswith(str(root)):
        return []

    try:
        if regex:
            cre = re.compile(pattern)
        else:
            cre = re.compile(re.escape(pattern), re.IGNORECASE)
    except re.error:
        return []

    hits: list[SearchHit] = []
    for fp in base.rglob("*"):
        if not fp.is_file() or _should_skip(fp.relative_to(root)):
            continue
        if fp.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".pyc"}:
            continue
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines = text.splitlines()
        rel = str(fp.relative_to(root)).replace("\\", "/")
        for i, line in enumerate(lines):
            if cre.search(line):
                before = lines[max(0, i - context) : i]
                after = lines[i + 1 : i + 1 + context]
                hits.append(
                    SearchHit(
                        path=rel,
                        line=i + 1,
                        text=line,
                        context_before=before,
                        context_after=after,
                    )
                )
                if len(hits) >= max_results:
                    return hits
    return hits
