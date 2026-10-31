"""Lightweight diagnostics collection (syntax / config heuristics).

This is a foundation layer — not a full LSP client. Real language servers
can be integrated later via configurable commands.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Diagnostic:
    path: str
    line: int
    severity: str  # error | warning | info
    message: str
    source: str = "hex"


def _python_syntax(path: Path, rel: str) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
        try:
            ast.parse(src)
        except SyntaxError as e:
            out.append(
                Diagnostic(
                    path=rel,
                    line=e.lineno or 1,
                    severity="error",
                    message=e.msg or "Syntax error",
                    source="python",
                )
            )
    except OSError:
        pass
    return out


def _json_syntax(path: Path, rel: str) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            json.loads(text)
        except json.JSONDecodeError as e:
            out.append(
                Diagnostic(
                    path=rel,
                    line=e.lineno or 1,
                    severity="error",
                    message=e.msg,
                    source="json",
                )
            )
    except OSError:
        pass
    return out


def collect_basic_diagnostics(
    project_root: Path,
    paths: list[str] | None = None,
    max_files: int = 40,
) -> list[Diagnostic]:
    """Scan a few project files for obvious syntax issues."""
    root = project_root.resolve()
    diagnostics: list[Diagnostic] = []
    candidates: list[Path] = []

    if paths:
        for p in paths:
            fp = (root / p).resolve()
            if fp.is_file() and str(fp).startswith(str(root)):
                candidates.append(fp)
    else:
        for pattern in ("**/*.py", "**/*.json"):
            for fp in root.glob(pattern):
                if any(part.startswith(".") for part in fp.parts):
                    continue
                if "node_modules" in fp.parts or "__pycache__" in fp.parts:
                    continue
                candidates.append(fp)
                if len(candidates) >= max_files:
                    break
            if len(candidates) >= max_files:
                break

    for fp in candidates[:max_files]:
        rel = str(fp.relative_to(root)).replace("\\", "/")
        if fp.suffix == ".py":
            diagnostics.extend(_python_syntax(fp, rel))
        elif fp.suffix == ".json":
            diagnostics.extend(_json_syntax(fp, rel))

    return diagnostics
