"""Project file listing and fuzzy match (no Textual dependency)."""

from __future__ import annotations

from pathlib import Path

IGNORE_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", "node_modules", ".venv", "venv",
    "dist", "build", ".tox", ".mypy_cache", ".pytest_cache", ".hex",
    ".idea", ".vscode",
}
IGNORE_SUFFIXES = {
    ".pyc", ".pyo", ".so", ".dll", ".exe", ".png", ".jpg", ".jpeg", ".gif",
    ".webp", ".ico", ".pdf", ".zip", ".tar", ".gz", ".woff", ".woff2",
}


def list_project_files(root: Path, limit: int = 400) -> list[str]:
    root = root.resolve()
    out: list[str] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if any(part in IGNORE_DIRS for part in rel.parts):
            continue
        if any(part.startswith(".") for part in rel.parts):
            continue
        if p.suffix.lower() in IGNORE_SUFFIXES:
            continue
        try:
            if p.stat().st_size > 1_500_000:
                continue
        except OSError:
            continue
        out.append(str(rel).replace("\\", "/"))
        if len(out) >= limit:
            break
    return sorted(out)


def fuzzy_score(query: str, path: str) -> int:
    q = query.lower()
    s = path.lower()
    if not q:
        return 0
    if q in s:
        return 1000 - s.index(q) - len(s) // 10
    i = 0
    for ch in s:
        if i < len(q) and ch == q[i]:
            i += 1
    if i == len(q):
        return 100 - len(s)
    return -1
