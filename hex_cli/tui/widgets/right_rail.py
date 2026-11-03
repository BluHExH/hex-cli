from __future__ import annotations

from textual.containers import VerticalScroll
from textual.widgets import Static


class RightRail(VerticalScroll):
    """Reference right column: Changes, Tools Activity, Session Info, Auto-save."""

    def __init__(self) -> None:
        super().__init__(id="right-rail")
        self._collapsed = False

    def compose(self):
        yield Static(id="right-body")

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
            hdr = f"[bold]Changes[/]  [dim]{len(ch)} files[/]            [dim]⋯[/]"
            lines = []
            for path, delta in ch[:10]:
                color = "green" if str(delta).startswith("+") else "red"
                lines.append(f"  [dim]📄[/] {path}  [{color}]{delta}[/]")
            ch_block = "\n".join(lines)
        else:
            hdr = "[bold]Changes[/]  [dim]0 files[/]"
            ch_block = "  [dim]No changes yet[/]"
        if act:
            act_lines = "\n".join(
                f"  [{'green' if ok else 'red'}]●[/] {name}  [dim]{meta}[/]"
                for name, meta, ok in act[:10]
            )
        else:
            act_lines = "  [dim]No activity[/]"
        save = "[green]☑[/] Auto-save enabled" if auto_save else "[dim]☐ Auto-save off[/]"
        self.query_one("#right-body", Static).update(
            "\n".join(
                [
                    hdr,
                    ch_block,
                    "",
                    "[bold]Tools Activity[/]              [dim]▾[/]",
                    act_lines,
                    "",
                    "[bold]Session Info[/]                [dim]▾[/]",
                    f"  [dim]▣[/] Model: {model}",
                    f"  [dim]▤[/] Context: {context_line}",
                    f"  [dim]◷[/] Started: {started or '—'}",
                    f"  [dim]◷[/] Duration: {duration or '—'}",
                    "",
                    f"  {save}",
                ]
            )
        )

    def toggle(self) -> None:
        self._collapsed = not self._collapsed
        self.set_class(self._collapsed, "collapsed")
        self.display = not self._collapsed
