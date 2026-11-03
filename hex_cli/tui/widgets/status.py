from __future__ import annotations

from textual.widgets import Static


class StatusBar(Static):
    def __init__(self) -> None:
        super().__init__(id="bottom-status")

    def set_status(self, *, ready: bool, model: str, workspace: str) -> None:
        dot = "[green]•[/] Ready" if ready else "[yellow]•[/] Working"
        self.update(
            f" [bold #a78bfa]HEX[/]  {dot}  {model}  [dim]{workspace}[/]     "
            f"[dim]^P palette  ^B panels  ^N new  Enter submit  Esc cancel[/]"
        )
