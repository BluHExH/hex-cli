"""Load custom slash commands from markdown templates.

Layout:
  ~/.hex/commands/<name>.md
  <project>/.hex/commands/<name>.md

Frontmatter: description, agent (optional)
Body: prompt template with {{args}} and {{argN}} placeholders.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from hex_cli.config import get_config_dir

# Built-in commands that cannot be overridden
RESERVED = {
    "help", "exit", "quit", "clear", "status", "new", "sessions", "session",
    "connect", "models", "model", "providers", "provider", "disconnect",
    "settings", "plan", "build", "explore", "agent", "agents", "diff",
    "review", "undo", "tools", "permissions", "init", "save", "history",
    "mcp", "skills", "worktree", "lsp",
}


@dataclass
class CustomCommand:
    name: str
    description: str
    template: str
    agent: str | None
    path: Path
    source: str  # global | project

    def render(self, args: str) -> str:
        text = self.template
        text = text.replace("{{args}}", args)
        parts = args.split()
        for i, p in enumerate(parts, 1):
            text = text.replace(f"{{{{arg{i}}}}}", p)
        # Clear unused placeholders
        text = re.sub(r"\{\{arg\d+\}\}", "", text)
        return text.strip()


def _parse(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip().lower()] = v.strip().strip("\"'")
    return meta, parts[2].strip()


class CommandLoader:
    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root.resolve() if project_root else None
        self.commands: dict[str, CustomCommand] = {}

    def reload(self) -> int:
        self.commands.clear()
        self._load_dir(get_config_dir() / "commands", "global")
        if self.project_root:
            self._load_dir(self.project_root / ".hex" / "commands", "project")
        return len(self.commands)

    def _load_dir(self, directory: Path, source: str) -> None:
        if not directory.is_dir():
            return
        for path in sorted(directory.glob("*.md")):
            name = path.stem.lower().lstrip("/")
            if not re.match(r"^[a-z][a-z0-9_-]*$", name):
                continue
            if name in RESERVED:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            meta, body = _parse(text)
            if not body:
                continue
            self.commands[name] = CustomCommand(
                name=name,
                description=meta.get("description") or body[:80],
                template=body,
                agent=meta.get("agent"),
                path=path,
                source=source,
            )

    def get(self, name: str) -> CustomCommand | None:
        return self.commands.get(name.lstrip("/").lower())

    def list_commands(self) -> list[CustomCommand]:
        return sorted(self.commands.values(), key=lambda c: c.name)
