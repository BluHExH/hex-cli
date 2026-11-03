from __future__ import annotations

from textual.containers import VerticalScroll
from textual.widgets import Static


class RightRail(VerticalScroll):
    """Right panel: changes, tool activity, session info."""

    def __init__(self) -> None:
        super().__init__(id="right-rail")
        self._collapsed = False

    def compose(self):
        yield Static("", id="right-body")

    def set_data(
        self,
        *,
        changes: list[tuple[str, str]] | None = None,
        activities: list[tuple[str, str, bool]] | None = None,
        model: str = "",
        context_line: str = "",
        started: str = "",
        duration: str = "",
        auto_save: bool = True,
    ) -> None:
        ch = changes or []
        act = activities or []
        if ch:
            ch_lines = "\n".join(f"  {path}  [green]{delta}[/]" for path, delta in ch[:12])
            ch_hdr = f"Changes  {len(ch)} files"
        else:
            ch_lines = "  [dim]No file changes[/]"
            ch_hdr = "Changes"
        if act:
            act_lines = "\n".join(
                f"  [{'green' if ok else 'red'}]•[/] {name}  [dim]{meta}[/]" for name, meta, ok in act[:12]
            )
        else:
            act_lines = "  [dim]No tool activity[/]"
        body = self.query_one("#right-body", Static)
        body.update(
            f"[bold]{ch_hdr}[/]\n{ch_lines}\n\n"
            f"[bold]Tools Activity[/]\n{act_lines}\n\n"
            f"[bold]Session Info[/]\n"
            f"  Model: {model}\n"
            f"  Context: {context_line}\n"
            f"  Started: {started or '—'}\n"
            f"  Duration: {duration or '—'}\n\n"
            f"  [{'green' if auto_save else 'yellow'}]•[/] Auto-save {'enabled' if auto_save else 'off'}"
        )

    def toggle(self) -> None:
        self._collapsed = not self._collapsed
        self.set_class(self._collapsed, "collapsed")
        self.display = not self._collapsed
