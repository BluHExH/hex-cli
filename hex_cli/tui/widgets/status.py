from __future__ import annotations

from textual.widgets import Static


class StatusBar(Static):
    """Bottom bar: brand · Ready · model · path · shortcuts (reference order)."""

    def __init__(self) -> None:
        super().__init__(id="bottom-status")

    def set_status(self, *, ready: bool, model: str, workspace: str) -> None:
        state = "[green]●[/] Ready" if ready else "[yellow]●[/] Working"
        path = workspace if len(workspace) < 36 else "…" + workspace[-34:]
        self.update(
            f"[bold #a78bfa]◆ HEX[/]   {state}   [green]●[/] {model}   [dim]{path}[/]"
            f"          [dim]Ctrl+P Palette  Ctrl+B Sidebar  Enter Submit  Esc Cancel[/]"
        )
