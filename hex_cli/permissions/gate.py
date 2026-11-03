from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class PermissionDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    PROMPT = "prompt"


@dataclass
class PermissionRequest:
    tool: str
    action: str
    target: str
    detail: str = ""


class PermissionGate:
    """Tool boundary authorization (Skill: permission service concept)."""

    def __init__(
        self,
        mode: str = "prompt",
        prompter: Callable[[PermissionRequest], bool] | None = None,
    ) -> None:
        self.mode = mode
        self.prompter = prompter
        self.auto_allow = {"read_file", "list_dir", "search_files"}

    def decide(self, req: PermissionRequest) -> PermissionDecision:
        if self.mode == "allow":
            return PermissionDecision.ALLOW
        if self.mode == "deny":
            return PermissionDecision.DENY
        if req.tool in self.auto_allow and req.action in {"read", "list", "search"}:
            return PermissionDecision.ALLOW
        if self.prompter is not None:
            return PermissionDecision.ALLOW if self.prompter(req) else PermissionDecision.DENY
        # Default interactive TUI will inject prompter; headless denies sensitive ops
        if req.tool in self.auto_allow:
            return PermissionDecision.ALLOW
        return PermissionDecision.DENY
