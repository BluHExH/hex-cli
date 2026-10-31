"""Unified tool registry for the HEX coding agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    risk: str = "low"

    def to_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


TOOL_SPECS: list[ToolSpec] = [
    ToolSpec(
        name="list_files",
        description="List files and directories under a relative path inside the project.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "default": "."},
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
                "offset": {"type": "integer"},
                "limit": {"type": "integer"},
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
        description="Create or overwrite a file. Requires approval.",
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
        description="Search-and-replace edit. Requires approval.",
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
        description="Apply a unified-diff style patch. Requires approval.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "patch": {"type": "string"},
            },
            "required": ["path", "patch"],
        },
        risk="medium",
    ),
    ToolSpec(
        name="create_directory",
        description="Create a directory. Requires approval.",
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
        risk="medium",
    ),
    ToolSpec(
        name="run_command",
        description="Run a shell command. Requires approval.",
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
        description="Run the project test suite.",
        parameters={
            "type": "object",
            "properties": {"args": {"type": "string", "default": ""}},
        },
        risk="medium",
    ),
    ToolSpec(
        name="git_status",
        description="Show git status.",
        parameters={"type": "object", "properties": {}},
        risk="low",
    ),
    ToolSpec(
        name="git_diff",
        description="Show git diff.",
        parameters={
            "type": "object",
            "properties": {"staged": {"type": "boolean", "default": False}},
        },
        risk="low",
    ),
    ToolSpec(
        name="project_overview",
        description="Summarize project structure and key config files.",
        parameters={"type": "object", "properties": {}},
        risk="low",
    ),
    ToolSpec(
        name="detect_project_type",
        description="Detect project language/ecosystem.",
        parameters={"type": "object", "properties": {}},
        risk="low",
    ),
]


def openai_tool_schemas() -> list[dict[str, Any]]:
    return [s.to_openai_schema() for s in TOOL_SPECS]


def tool_names() -> list[str]:
    return [s.name for s in TOOL_SPECS]


def get_tool_spec(name: str) -> ToolSpec | None:
    for s in TOOL_SPECS:
        if s.name == name:
            return s
    return None


def list_tools_for_display() -> list[dict[str, str]]:
    return [
        {"name": s.name, "description": s.description, "risk": s.risk}
        for s in TOOL_SPECS
    ]
