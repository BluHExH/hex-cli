from __future__ import annotations

from textual.widgets import Static

from hex_cli import __version__


class AppHeader(Static):
    """Full-width top bar: brand | path | model · Agent."""

    def __init__(self) -> None:
        super().__init__(id="top-header")

    def set_meta(
        self,
        *,
        workspace: str,
        model: str,
        provider: str,
        agent_status: str = "Agent",
        branch: str = "",
        commits: int = 0,
    ) -> None:
        # Reference: left brand · center path | branch · right model + Agent
        path = workspace if len(workspace) < 44 else "…" + workspace[-42:]
        branch_part = f" [dim]│[/] [dim]⎇[/] [dim]{branch}[/] [dim]{commits}[/]" if branch else ""
        self.update(
            f"[bold #a78bfa]⬡ HEX[/] [dim]CLI[/]          "
            f"[dim]{path}[/]{branch_part}                    "
            f"[green]●[/] {provider}/{model}   [green]●[/] {agent_status}   [dim]⚙[/]"
        )
