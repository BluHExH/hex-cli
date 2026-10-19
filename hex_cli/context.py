"""Project context gathering for the agent."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hex_cli.tools.filesystem import SKIP_DIRS

IMPORTANT_NAMES = {
    "README.md",
    "README.rst",
    "README.txt",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "Makefile",
    "Dockerfile",
    ".gitignore",
    "tsconfig.json",
    "Cargo.lock",
}


def discover_project_summary(root: Path, max_files: int = 80) -> str:
    """Build a concise textual summary of the project layout."""
    root = root.resolve()
    lines: list[str] = [f"Project root: {root}"]

    # Important top-level files
    top = []
    for p in sorted(root.iterdir()):
        if p.name.startswith(".") and p.name not in (".gitignore",):
            if p.name == ".git":
                top.append(".git/ (repository)")
            continue
        if p.name in SKIP_DIRS:
            continue
        if p.is_file():
            top.append(p.name)
        else:
            top.append(p.name + "/")
    lines.append("Top-level: " + ", ".join(top[:40]))

    # Collect important files
    important: list[str] = []
    for name in IMPORTANT_NAMES:
        candidate = root / name
        if candidate.is_file():
            important.append(name)
    if important:
        lines.append("Key files: " + ", ".join(important))

    # Shallow tree of source-ish directories
    src_candidates = ["src", "lib", "app", "hex_cli", "pkg", "internal", "cmd"]
    for name in src_candidates:
        d = root / name
        if d.is_dir():
            count = 0
            sample = []
            for p in d.rglob("*"):
                if any(part in SKIP_DIRS for part in p.parts):
                    continue
                if p.is_file() and p.suffix in {
                    ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".cs"
                }:
                    sample.append(p.relative_to(root).as_posix())
                    count += 1
                    if len(sample) >= 15:
                        break
            lines.append(f"{name}/ ({count}+ source files): {', '.join(sample)}")

    return "\n".join(lines)


def load_key_file_snippets(root: Path, max_chars: int = 12_000) -> str:
    """Load short snippets from key config/readme files."""
    root = root.resolve()
    parts: list[str] = []
    budget = max_chars

    for name in ("README.md", "pyproject.toml", "package.json", "Cargo.toml"):
        fp = root / name
        if not fp.is_file():
            continue
        try:
            text = fp.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        snippet = text[: min(3000, budget)]
        parts.append(f"--- {name} ---\n{snippet}")
        budget -= len(snippet)
        if budget < 500:
            break

    return "\n\n".join(parts) if parts else "(no key files found)"
