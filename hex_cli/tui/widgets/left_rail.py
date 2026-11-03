from __future__ import annotations

from textual.containers import VerticalScroll
from textual.widgets import Static


class LeftRail(VerticalScroll):
    """Left navigation: session, workspace, context, tools, permissions, recent."""

    def __init__(self) -> None:
        super().__init__(id="left-rail")
        self._collapsed = False

    def compose(self):
        yield Static("", id="left-body")

    def set_data(
        self,
        *,
        workspace: str,
        context_chars: int = 0,
        context_max: int = 120_000,
        tool_count: int = 0,
        permission_mode: str = "prompt",
        recent_files: list[str] | None = None,
    ) -> None:
        pct = 0
        if context_max > 0:
            pct = min(100, int(100 * context_chars / context_max))
        bar_filled = max(0, min(10, pct // 10))
        bar = "█" * bar_filled + "░" * (10 - bar_filled)
        files = recent_files or []
        file_lines = "\n".join(f"  {f}" for f in files[:6]) or "  [dim]—[/]"
        auto = "Auto-approve: Read" if permission_mode in {"allow", "prompt"} else permission_mode
        body = self.query_one("#left-body", Static)
        body.update(
            f"[bold]Session[/]\n"
            f"  New Session          [dim]^N[/]\n"
            f"  Switch Session       [dim]^O[/]\n"
            f"  Manage Sessions\n\n"
            f"[bold]Workspace[/]\n"
            f"  [dim]{workspace}[/]\n\n"
            f"[bold]Context[/]\n"
            f"  {pct}% · {context_chars // 1000}K / {context_max // 1000}K\n"
            f"  [green]{bar}[/]\n\n"
            f"[bold]Tools[/]\n"
            f"  {tool_count} tools available\n\n"
            f"[bold]Permissions[/]\n"
            f"  [green]•[/] {auto}\n\n"
            f"[bold]Recent Files[/]\n"
            f"{file_lines}\n\n"
            f"[dim]Help · Settings[/]"
        )

    def toggle(self) -> None:
        self._collapsed = not self._collapsed
        self.set_class(self._collapsed, "collapsed")
        self.display = not self._collapsed
