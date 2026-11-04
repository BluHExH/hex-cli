"""Slash command registry for the OpenCode-style TUI (mirrors OpenCode TUI docs)."""
from __future__ import annotations

CANONICAL: list[tuple[str, str]] = [
    ("new", "Start a new session"),
    ("sessions", "List and switch between sessions"),
    ("models", "List available models"),
    ("undo", "Undo last message"),
    ("compact", "Compact the current session"),
    ("details", "Toggle tool execution details"),
    ("help", "Show the command list"),
    ("exit", "Exit HEX"),
]

ALIASES: dict[str, str] = {
    "clear": "new",
    "resume": "sessions",
    "continue": "sessions",
    "summarize": "compact",
    "quit": "exit",
    "q": "exit",
}


def match(prefix: str) -> list[tuple[str, str]]:
    """Prefix matches over canonical commands, e.g. match('/mo')."""
    p = prefix.lstrip("/").strip().lower()
    if not p:
        return list(CANONICAL)
    return [(name, desc) for name, desc in CANONICAL if name.startswith(p)]


def resolve(text: str) -> tuple[str | None, str]:
    """Split '/cmd rest' into (canonical name, rest). Returns (None, …) if unknown."""
    body = text.strip()
    if not body.startswith("/"):
        return None, body
    parts = body[1:].split(maxsplit=1)
    cmd = parts[0].lower() if parts else ""
    rest = parts[1] if len(parts) > 1 else ""
    cmd = ALIASES.get(cmd, cmd)
    if cmd in dict(CANONICAL):
        return cmd, rest
    return None, rest
