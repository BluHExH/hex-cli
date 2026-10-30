"""Permission-first security model for HEX CLI.

Every file write, command execution, and high-impact Git action requires
explicit user approval unless the user has configured a more permissive mode.
Path traversal and symlink escapes are rejected.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

from hex_cli.config import AppConfig, PermissionMode


class ActionType(str, Enum):
    READ_FILE = "read_file"
    CREATE_FILE = "create_file"
    MODIFY_FILE = "modify_file"
    DELETE_FILE = "delete_file"
    CREATE_DIRECTORY = "create_directory"
    RUN_COMMAND = "run_command"
    GIT_COMMIT = "git_commit"
    GIT_PUSH = "git_push"
    DEPLOYMENT = "deployment"
    OTHER = "other"


@dataclass
class PermissionRequest:
    action: ActionType
    description: str
    path: str | None = None
    detail: str | None = None
    high_impact: bool = False


@dataclass
class PermissionResult:
    allowed: bool
    reason: str = ""


HIGH_IMPACT_PATTERNS = [
    re.compile(r"\brm\s+(-[a-zA-Z]*f|-[a-zA-Z]*r)", re.I),
    re.compile(r"\bdel\s+/[sf]", re.I),
    re.compile(r"\brmdir\s+/s", re.I),
    re.compile(r"\bgit\s+push\b", re.I),
    re.compile(r"\bgit\s+reset\s+--hard\b", re.I),
    re.compile(r"\bgit\s+clean\s+-f", re.I),
    re.compile(r"\bformat\s+[a-z]:", re.I),
    re.compile(r"\bshutdown\b", re.I),
    re.compile(r"\breboot\b", re.I),
    re.compile(r"\bmkfs\b", re.I),
    re.compile(r"\bdd\s+if=", re.I),
    re.compile(r">\s*/dev/", re.I),
    re.compile(r"\bcurl\b.*\|\s*(ba)?sh", re.I),
    re.compile(r"\bwget\b.*\|\s*(ba)?sh", re.I),
    re.compile(r"\binvoke-webrequest\b.*\|\s*iex", re.I),
    re.compile(r"\bpip\s+install\b", re.I),
    re.compile(r"\bnpm\s+install\b", re.I),
    re.compile(r"\bdocker\s+(run|exec|rm|rmi|system)", re.I),
]

BLOCKED_COMMAND_FRAGMENTS = [
    "rm -rf /",
    "rm -rf /*",
    "del /s /q c:\\",
    "format c:",
    ":(){:|:&};:",
]


class PermissionManager:
    """Evaluates and requests approval for agent actions."""

    def __init__(
        self,
        config: AppConfig,
        project_root: Path,
        ask_fn: Callable[[PermissionRequest], bool] | None = None,
    ):
        self.config = config
        self.project_root = project_root.resolve()
        self._ask = ask_fn

    def set_ask_callback(self, fn: Callable[[PermissionRequest], bool]) -> None:
        self._ask = fn

    def resolve_safe_path(self, relative_or_abs: str) -> Path:
        """Resolve a path and ensure it stays inside project_root."""
        raw = Path(relative_or_abs)
        if raw.is_absolute():
            resolved = raw.resolve()
        else:
            resolved = (self.project_root / raw).resolve()
        try:
            resolved.relative_to(self.project_root)
        except ValueError:
            raise PermissionError(
                f"Path escapes project root: {relative_or_abs!r} "
                f"(resolved to {resolved})"
            )
        if resolved.exists() or resolved.is_symlink():
            real = resolved.resolve()
            try:
                real.relative_to(self.project_root)
            except ValueError:
                raise PermissionError(
                    f"Symlink escape detected: {relative_or_abs!r} → {real}"
                )
        return resolved

    def is_path_safe(self, path_str: str) -> bool:
        try:
            self.resolve_safe_path(path_str)
            return True
        except PermissionError:
            return False

    def _mode_for(self, action: ActionType):
        mapping = {
            ActionType.READ_FILE: self.config.permissions.read_files,
            ActionType.CREATE_FILE: self.config.permissions.create_files,
            ActionType.MODIFY_FILE: self.config.permissions.modify_files,
            ActionType.DELETE_FILE: self.config.permissions.delete_files,
            ActionType.CREATE_DIRECTORY: self.config.permissions.create_files,
            ActionType.RUN_COMMAND: self.config.permissions.run_commands,
            ActionType.GIT_COMMIT: self.config.permissions.git_commit,
            ActionType.GIT_PUSH: self.config.permissions.git_push,
            ActionType.DEPLOYMENT: self.config.permissions.deployment,
        }
        return mapping.get(action, "ask")

    def is_high_impact_command(self, command: str) -> bool:
        cmd_lower = command.lower().strip()
        for blocked in BLOCKED_COMMAND_FRAGMENTS:
            if blocked in cmd_lower:
                return True
        for pat in HIGH_IMPACT_PATTERNS:
            if pat.search(command):
                return True
        return False

    def check(
        self,
        action: ActionType,
        description: str,
        path: str | None = None,
        detail: str | None = None,
        force_ask: bool = False,
    ) -> PermissionResult:
        if path is not None:
            try:
                self.resolve_safe_path(path)
            except PermissionError as e:
                return PermissionResult(False, str(e))
        high_impact = False
        if action == ActionType.RUN_COMMAND and detail:
            high_impact = self.is_high_impact_command(detail)
        if action in (ActionType.GIT_PUSH, ActionType.DEPLOYMENT, ActionType.DELETE_FILE):
            high_impact = True
        mode = self._mode_for(action)
        if mode == "deny":
            return PermissionResult(False, f"Action '{action.value}' is denied by configuration")
        if mode == "allow" and not high_impact and not force_ask:
            return PermissionResult(True, "allowed by configuration")
        request = PermissionRequest(
            action=action,
            description=description,
            path=path,
            detail=detail,
            high_impact=high_impact,
        )
        if self._ask is None:
            if high_impact or mode == "ask":
                return PermissionResult(
                    False,
                    "Interactive approval required but no UI callback is available",
                )
            return PermissionResult(True, "non-interactive allow")
        approved = self._ask(request)
        if approved:
            return PermissionResult(True, "user approved")
        return PermissionResult(False, "user rejected")
