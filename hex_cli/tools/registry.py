from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from hex_cli.permissions.gate import PermissionDecision, PermissionGate, PermissionRequest
from hex_cli.tools.filesystem import FileTools
from hex_cli.tools.shell import ShellTool


@dataclass
class ToolResult:
    ok: bool
    output: str
    error: str = ""


class ToolRegistry:
    def __init__(self, root: Path, gate: PermissionGate) -> None:
        self.root = root.resolve()
        self.gate = gate
        self.fs = FileTools(self.root)
        self.shell = ShellTool(self.root)
        self._handlers: dict[str, Callable[[dict[str, Any]], str]] = {
            "read_file": lambda a: self.fs.read_file(a["path"]),
            "write_file": lambda a: self.fs.write_file(a["path"], a.get("content", "")),
            "list_dir": lambda a: self.fs.list_dir(a.get("path", ".")),
            "search_files": lambda a: self.fs.search_files(a["pattern"], a.get("path", ".")),
            "run_shell": lambda a: self.shell.run(a["command"], use_shell=bool(a.get("use_shell", False))),
        }

    def schemas(self) -> list[dict[str, Any]]:
        return [
            {"name": "read_file", "description": "Read a workspace file", "parameters": {"path": "string"}},
            {"name": "write_file", "description": "Write a workspace file", "parameters": {"path": "string", "content": "string"}},
            {"name": "list_dir", "description": "List directory entries", "parameters": {"path": "string"}},
            {"name": "search_files", "description": "Regex search in files", "parameters": {"pattern": "string", "path": "string"}},
            {"name": "run_shell", "description": "Run a shell command in workspace", "parameters": {"command": "string"}},
        ]

    def execute(self, name: str, args: dict[str, Any]) -> ToolResult:
        if name not in self._handlers:
            return ToolResult(False, "", f"unknown tool: {name}")
        action = {
            "read_file": "read",
            "write_file": "write",
            "list_dir": "list",
            "search_files": "search",
            "run_shell": "shell",
        }.get(name, "unknown")
        target = str(args.get("path") or args.get("command") or "")
        decision = self.gate.decide(PermissionRequest(tool=name, action=action, target=target))
        if decision != PermissionDecision.ALLOW:
            return ToolResult(False, "", f"permission denied: {name} {target}")
        try:
            out = self._handlers[name](args)
            return ToolResult(True, out)
        except Exception as exc:  # noqa: BLE001 — tool boundary
            return ToolResult(False, "", str(exc))
