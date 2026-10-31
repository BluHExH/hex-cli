"""Unified tool registry for the HEX coding agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    risk: str = "low"  # low | medium | high

    def to_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


# Canonical tool definitions (source of truth for model schemas)
TOOL_SPECS: list[ToolSpec] = [
    ToolSpec(
        name="list_files",
        description="List files and directories under a relative path inside the project.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path", "default": "."},
                "recursive": {"type": "boolean", "default": False},
            },
        },
        risk="low",
    ),
    ToolSpec(
        name="read_file",
        description="Read a text file inside the project (optional line range).",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "offset": {"type": "integer", "description": "1-based start line"},
                "limit": {"type": "integer", "description": "Max lines"},
            },
            "required": ["path"],
        },
        risk="low",
    ),
    ToolSpec(
        name="search_text",
        description="Search for a text/regex pattern across project source files.",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string", "default": "."},
                "max_results": {"type": "integer", "default": 30},
            },
            "required": ["pattern"],
        },
        risk="low",
    ),
    ToolSpec(
        name="glob",
        description="Find files matching a glob pattern (e.g. **/*.py).",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string", "default": "."},
                "max_results": {"type": "integer", "default": 100},
            },
            "required": ["pattern"],
        },
        risk="low",
    ),
    ToolSpec(
        name="write_file",
        description="Create a new file or overwrite an existing one. Requires approval.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
        risk="medium",
    ),
    ToolSpec(
        name="edit_file",
        description="Search-and-replace edit on an existing file. Requires approval.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_string": {"type": "string"},
                "new_string": {"type": "string"},
                "replace_all": {"type": "boolean", "default": False},
            },
            "required": ["path", "old_string", "new_string"],
        },
        risk="medium",
    ),
    ToolSpec(
        name="apply_patch",
        description="Apply a unified-diff style patch to a file. Requires approval.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "patch": {"type": "string", "description": "Unified diff body"},
            },
            "required": ["path", "patch"],
        },
        risk="medium",
    ),
    ToolSpec(
        name="create_directory",
        description="Create a directory (and parents). Requires approval.",
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
        risk="medium",
    ),
    ToolSpec(
        name="run_command",
        description="Run a shell command in the project directory. Requires approval.",
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "timeout": {"type": "number"},
            },
            "required": ["command"],
        },
        risk="high",
    ),
    ToolSpec(
        name="run_tests",
        description="Run the project test suite (pytest by default).",
        parameters={
            "type": "object",
            "properties": {"args": {"type": "string", "default": ""}},
        },
        risk="medium",
    ),
    ToolSpec(
        name="git_status",
        description="Show git status for the repository.",
        parameters={"type": "object", "properties": {}},
        risk="low",
    ),
    ToolSpec(
        name="git_diff",
        description="Show git diff (unstaged by default).",
        parameters={
            "type": "object",
            "properties": {"staged": {"type": "boolean", "default": False}},
        },
        risk="low",
    ),
    ToolSpec(
        name="git_branches",
        description="List local git branches and the current branch.",
        parameters={"type": "object", "properties": {}},
        risk="low",
    ),
    ToolSpec(
        name="git_log",
        description="Show recent commit history.",
        parameters={
            "type": "object",
            "properties": {"max_count": {"type": "integer", "default": 15}},
        },
        risk="low",
    ),
    ToolSpec(
        name="git_stage",
        description="Stage selected files (or all). Requires approval.",
        parameters={
            "type": "object",
            "properties": {
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Paths to stage; omit for all",
                }
            },
        },
        risk="medium",
    ),
    ToolSpec(
        name="git_commit",
        description="Create a git commit with a message. Requires approval. Does not push.",
        parameters={
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        },
        risk="high",
    ),
    ToolSpec(
        name="git_checkout",
        description="Switch or create a local branch. Requires approval. Never force-discards.",
        parameters={
            "type": "object",
            "properties": {
                "branch": {"type": "string"},
                "create": {"type": "boolean", "default": False},
            },
            "required": ["branch"],
        },
        risk="medium",
    ),
    ToolSpec(
        name="project_overview",
        description="Summarize project structure, type, and key config files.",
        parameters={"type": "object", "properties": {}},
        risk="low",
    ),
    ToolSpec(
        name="detect_project_type",
        description="Detect project language/ecosystem (Python, Node, Rust, Go, Java, etc.).",
        parameters={"type": "object", "properties": {}},
        risk="low",
    ),
]


def openai_tool_schemas(allowed: set[str] | frozenset[str] | None = None) -> list[dict[str, Any]]:
    specs = TOOL_SPECS
    if allowed is not None:
        specs = [s for s in TOOL_SPECS if s.name in allowed]
    return [s.to_openai_schema() for s in specs]


def tool_names() -> list[str]:
    return [s.name for s in TOOL_SPECS]


def get_tool_spec(name: str) -> ToolSpec | None:
    for s in TOOL_SPECS:
        if s.name == name:
            return s
    return None


def list_tools_for_display(allowed: set[str] | frozenset[str] | None = None) -> list[dict[str, str]]:
    specs = TOOL_SPECS
    if allowed is not None:
        specs = [s for s in TOOL_SPECS if s.name in allowed]
    return [
        {"name": s.name, "description": s.description, "risk": s.risk}
        for s in specs
    ]
