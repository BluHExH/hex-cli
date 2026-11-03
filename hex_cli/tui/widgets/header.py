from __future__ import annotations

from textual.widgets import Static

from hex_cli import __version__


class AppHeader(Static):
    def __init__(self) -> None:
        super().__init__(id="top-header")

    def set_meta(self, *, workspace: str, model: str, provider: str, agent_status: str = "Agent") -> None:
        self.update(
            f"[bold #a78bfa]HEX[/] [dim]CLI {__version__}[/]   "
            f"[dim]{workspace}[/]   "
            f"[green]•[/] {provider}/{model}   [green]•[/] {agent_status}"
        )
