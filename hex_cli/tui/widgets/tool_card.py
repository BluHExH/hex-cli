"""Expandable tool execution cards for the HEX chat panel."""

from __future__ import annotations

import time
from enum import Enum

try:
    from textual.app import ComposeResult
    from textual.containers import Vertical
    from textual.widgets import Static
    HAS_TEXTUAL = True
except ImportError:
    HAS_TEXTUAL = False
    ComposeResult = object  # type: ignore
    class Static:  # type: ignore
        def __init__(self, *a, **k): pass
        def update(self, *a, **k): pass
        def query_one(self, *a, **k):
            raise RuntimeError('no textual')


class ToolCardState(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DENIED = "denied"
    CANCELLED = "cancelled"


_STATE_STYLE = {
    ToolCardState.RUNNING: "yellow",
    ToolCardState.COMPLETED: "green",
    ToolCardState.FAILED: "red",
    ToolCardState.DENIED: "magenta",
    ToolCardState.CANCELLED: "dim",
}


class ToolCard(Static):
    """Compact, expandable tool execution summary."""

    def __init__(
        self,
        tool_name: str,
        risk: str = "low",
        args_summary: str = "",
        card_id: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.risk = risk
        self.args_summary = args_summary
        self.state = ToolCardState.RUNNING
        self.output = ""
        self.error = ""
        self.started = time.time()
        self.duration_ms = 0
        self.expanded = False
        self._card_id = card_id or f"tool-{tool_name}-{int(self.started * 1000) % 100000}"

    def compose(self) -> ComposeResult:
        with Vertical(id=self._card_id):
            yield Static(self._header(), id=f"{self._card_id}-header")
            yield Static("", id=f"{self._card_id}-body", classes="tool-card-body")

    def _header(self) -> str:
        color = _STATE_STYLE.get(self.state, "white")
        dur = f" {self.duration_ms}ms" if self.duration_ms else ""
        return (
            f"[{color}]● {self.state.value}[/{color}] "
            f"[bold]{self.tool_name}[/bold] "
            f"[dim]({self.risk}){dur}[/dim] "
            f"{self.args_summary[:60]}"
        )

    def set_state(
        self,
        state: ToolCardState,
        output: str = "",
        error: str = "",
    ) -> None:
        self.state = state
        if output:
            self.output = output
        if error:
            self.error = error
        self.duration_ms = int((time.time() - self.started) * 1000)
        self._refresh_view()

    def toggle(self) -> None:
        self.expanded = not self.expanded
        self._refresh_view()

    def _refresh_view(self) -> None:
        try:
            header = self.query_one(f"#{self._card_id}-header", Static)
            header.update(self._header())
            body = self.query_one(f"#{self._card_id}-body", Static)
            if self.expanded:
                parts = []
                if self.args_summary:
                    parts.append(f"[dim]input:[/dim] {self.args_summary}")
                if self.output:
                    parts.append(f"[dim]output:[/dim]\n{self.output[:2000]}")
                if self.error:
                    parts.append(f"[red]error:[/red] {self.error[:500]}")
                body.update("\n".join(parts) if parts else "[dim](no details)[/dim]")
            else:
                body.update("")
        except Exception:
            pass

    def as_text(self) -> str:
        """Plain-text fallback for ChatLog when widgets aren't mounted."""
        icon = {
            ToolCardState.RUNNING: "…",
            ToolCardState.COMPLETED: "✓",
            ToolCardState.FAILED: "✗",
            ToolCardState.DENIED: "⊘",
            ToolCardState.CANCELLED: "–",
        }.get(self.state, "·")
        line = f"{icon} {self.tool_name} [{self.state.value}]"
        if self.duration_ms:
            line += f" {self.duration_ms}ms"
        if self.args_summary:
            line += f" — {self.args_summary[:80]}"
        if self.expanded and self.output:
            line += f"\n{self.output[:500]}"
        if self.error:
            line += f"\nerror: {self.error[:200]}"
        return line
