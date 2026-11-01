"""Expandable tool execution cards for the HEX conversation."""

from __future__ import annotations

import time
from enum import Enum

try:
    from textual.app import ComposeResult
    from textual.widgets import Static
    HAS_TEXTUAL = True
except ImportError:
    HAS_TEXTUAL = False
    ComposeResult = object  # type: ignore

    class Static:  # type: ignore
        def __init__(self, *a, **k):
            pass

        def update(self, *a, **k):
            pass


class ToolCardState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DENIED = "denied"
    CANCELLED = "cancelled"


_STATUS_ICON = {
    ToolCardState.PENDING: "·",
    ToolCardState.RUNNING: "⟳",
    ToolCardState.COMPLETED: "✓",
    ToolCardState.FAILED: "✗",
    ToolCardState.DENIED: "⊘",
    ToolCardState.CANCELLED: "–",
}

_STATUS_COLOR = {
    ToolCardState.PENDING: "dim",
    ToolCardState.RUNNING: "yellow",
    ToolCardState.COMPLETED: "green",
    ToolCardState.FAILED: "red",
    ToolCardState.DENIED: "magenta",
    ToolCardState.CANCELLED: "dim",
}

# Human titles for known tools
TOOL_TITLES = {
    "read_file": "READ FILE",
    "write_file": "WRITE FILE",
    "edit_file": "EDIT FILE",
    "apply_patch": "APPLY PATCH",
    "list_directory": "LIST DIR",
    "search_files": "SEARCH",
    "grep": "GREP",
    "run_command": "SHELL",
    "run_tests": "TESTS",
    "git_status": "GIT STATUS",
    "git_diff": "GIT DIFF",
    "git_stage": "GIT STAGE",
    "git_commit": "GIT COMMIT",
    "git_checkout": "GIT CHECKOUT",
    "create_directory": "MKDIR",
}


def status_from_string(s: str) -> ToolCardState:
    s = (s or "").lower()
    if s in ("running", "in_progress", "start"):
        return ToolCardState.RUNNING
    if s in ("ok", "completed", "success", "done"):
        return ToolCardState.COMPLETED
    if s in ("error", "failed", "fail"):
        return ToolCardState.FAILED
    if s in ("skipped", "denied", "rejected"):
        return ToolCardState.DENIED
    if s in ("cancelled", "canceled"):
        return ToolCardState.CANCELLED
    if s in ("pending", "waiting"):
        return ToolCardState.PENDING
    return ToolCardState.PENDING


class ToolCard(Static):
    """Clickable expandable summary of one tool execution."""

    can_focus = True

    def __init__(
        self,
        tool_name: str,
        detail: str = "",
        card_key: str | None = None,
        risk: str = "low",
        args_summary: str = "",
        **kwargs,
    ) -> None:
        # Drop unknown Textual kwargs that older call sites may pass via **kwargs only
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.risk = risk
        self.detail = detail or args_summary or ""
        self.state = ToolCardState.RUNNING
        self.output = ""
        self.error = ""
        self.started = time.time()
        self.duration_ms = 0
        self.expanded = False
        self.card_key = card_key or f"{tool_name}-{int(self.started * 1000)}"
        self.add_class("tool-card")
        self._render_body()

    def title(self) -> str:
        return TOOL_TITLES.get(self.tool_name, self.tool_name.upper().replace("_", " "))

    def set_state(
        self,
        state: ToolCardState | str,
        output: str = "",
        error: str = "",
    ) -> None:
        """Backward-compatible alias used by older tests."""
        self.set_status(state, output=output, error=error)

    def set_status(

        self,
        status: str | ToolCardState,
        *,
        detail: str | None = None,
        output: str = "",
        error: str = "",
    ) -> None:
        if isinstance(status, str):
            self.state = status_from_string(status)
        else:
            self.state = status
        if detail is not None and detail != "":
            self.detail = detail
        if output:
            self.output = output
        if error:
            self.error = error
        if self.state != ToolCardState.RUNNING:
            self.duration_ms = int((time.time() - self.started) * 1000)
        self._render_body()

    def toggle(self) -> None:
        self.expanded = not self.expanded
        self._render_body()

    def on_click(self) -> None:
        self.toggle()

    def on_key(self, event) -> None:  # noqa: ANN001
        if getattr(event, "key", None) in ("enter", "space"):
            event.prevent_default()
            event.stop()
            self.toggle()

    def _render_body(self) -> None:
        icon = _STATUS_ICON.get(self.state, "·")
        color = _STATUS_COLOR.get(self.state, "white")
        dur = f"  {self.duration_ms}ms" if self.duration_ms and self.state != ToolCardState.RUNNING else ""
        head = (
            f"[{color}]{icon}[/{color}] "
            f"[bold]{self.title()}[/bold]  "
            f"[dim]{self.detail[:90]}[/dim]  "
            f"[{color}]{self.state.value}[/{color}]{dur}"
        )
        if not self.expanded:
            head += "  [dim](click expand)[/dim]"
            self.update(head)
            return
        parts = [head, ""]
        if self.detail:
            parts.append(f"[dim]target[/dim]  {self.detail[:500]}")
        if self.output:
            out = self.output[:2500]
            if len(self.output) > 2500:
                out += f"\n… ({len(self.output) - 2500} more chars)"
            parts.append(f"[dim]output[/dim]\n{out}")
        if self.error:
            parts.append(f"[red]error[/red]  {self.error[:800]}")
        if not self.output and not self.error:
            parts.append("[dim](no output yet)[/dim]")
        self.update("\n".join(parts))

    def as_text(self) -> str:
        return f"{self.tool_name} [{self.state.value}] {self.detail}"
