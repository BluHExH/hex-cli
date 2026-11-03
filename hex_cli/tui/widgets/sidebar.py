from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static


class SessionSidebar(VerticalScroll):
    """Collapsible session / workspace sidebar."""

    def __init__(self, **kwargs) -> None:
        super().__init__(id="sidebar", **kwargs)
        self._collapsed = False

    def compose(self) -> ComposeResult:
        yield Static("", id="sidebar-body")

    def set_content(
        self,
        *,
        session_id: str,
        session_title: str,
        workspace: str,
        provider: str,
        model: str,
        permission_mode: str,
        change_count: int,
        sessions: list[tuple[str, str]] | None = None,
    ) -> None:
        lines = [
            "[bold #a78bfa]Workspace[/]",
            f"[dim]{workspace}[/]",
            "",
            "[bold #a78bfa]Session[/]",
            f"{session_title}",
            f"[dim]{session_id}[/]",
            "",
            "[bold #a78bfa]Model[/]",
            f"{provider} / {model}",
            "",
            "[bold #a78bfa]Permissions[/]",
            f"[dim]{permission_mode}[/]",
            "",
            "[bold #a78bfa]Changes[/]",
            f"[dim]{change_count} recorded[/]",
        ]
        if sessions:
            lines += ["", "[bold #a78bfa]Recent[/]"]
            for sid, title in sessions[:8]:
                mark = "•" if sid == session_id else " "
                lines.append(f"{mark} [dim]{sid}[/] {title[:18]}")
        body = self.query_one("#sidebar-body", Static)
        body.update("\n".join(lines))

    def toggle(self) -> bool:
        self._collapsed = not self._collapsed
        self.set_class(self._collapsed, "collapsed")
        self.display = not self._collapsed
        return self._collapsed
