"""Discover and load skills from global and project directories.

Skill format (directory-based, inspired by open conventions):
  skill-name/
    SKILL.md          # required — YAML frontmatter + markdown instructions
    # optional assets are listed but never executed automatically

Frontmatter keys: name, description, agents (list), version
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hex_cli.config import get_config_dir


@dataclass
class Skill:
    name: str
    description: str
    instructions: str
    path: Path
    agents: list[str] = field(default_factory=lambda: ["general", "build", "plan", "explore"])
    version: str = "1"
    source: str = "project"  # project | global

    def applies_to(self, agent: str) -> bool:
        if not self.agents:
            return True
        return agent.lower() in [a.lower() for a in self.agents]


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta: dict[str, Any] = {}
    for line in parts[1].splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip().lower()
        val = val.strip().strip("\"'")
        if key == "agents":
            # [build, plan] or build, plan
            val = val.strip("[]")
            meta[key] = [a.strip() for a in val.split(",") if a.strip()]
        else:
            meta[key] = val
    body = parts[2].strip()
    return meta, body


class SkillLoader:
    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root.resolve() if project_root else None
        self.skills: dict[str, Skill] = {}

    def global_dir(self) -> Path:
        return get_config_dir() / "skills"

    def project_dir(self) -> Path | None:
        if not self.project_root:
            return None
        return self.project_root / ".hex" / "skills"

    def reload(self) -> int:
        self.skills.clear()
        # Global first, project overrides
        self._load_dir(self.global_dir(), source="global")
        pd = self.project_dir()
        if pd:
            self._load_dir(pd, source="project")
        return len(self.skills)

    def _load_dir(self, directory: Path, source: str) -> None:
        if not directory.is_dir():
            return
        for child in sorted(directory.iterdir()):
            if not child.is_dir():
                continue
            skill_md = child / "SKILL.md"
            if not skill_md.is_file():
                # also accept skill.md
                skill_md = child / "skill.md"
            if not skill_md.is_file():
                continue
            # Path safety: must stay under directory
            try:
                skill_md.resolve().relative_to(directory.resolve())
            except ValueError:
                continue
            try:
                text = skill_md.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            meta, body = _parse_frontmatter(text)
            name = str(meta.get("name") or child.name).strip()
            if not re.match(r"^[a-zA-Z0-9_-]+$", name):
                continue
            skill = Skill(
                name=name,
                description=str(meta.get("description") or body[:120]),
                instructions=body,
                path=child,
                agents=list(meta.get("agents") or ["general", "build", "plan", "explore"]),
                version=str(meta.get("version") or "1"),
                source=source,
            )
            self.skills[name] = skill

    def list_skills(self, agent: str | None = None) -> list[Skill]:
        items = list(self.skills.values())
        if agent:
            items = [s for s in items if s.applies_to(agent)]
        return sorted(items, key=lambda s: s.name)

    def get(self, name: str) -> Skill | None:
        return self.skills.get(name)

    def instructions_for_agent(self, agent: str) -> str:
        """Concatenate skill instructions applicable to an agent."""
        parts = []
        for s in self.list_skills(agent):
            parts.append(f"### Skill: {s.name}\n{s.instructions}")
        return "\n\n".join(parts)
