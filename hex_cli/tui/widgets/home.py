from __future__ import annotations

from textual.widgets import Static

from hex_cli import __version__


class HomeScreen(Static):
    """Landing / empty-state panel."""

    def __init__(self, **kwargs) -> None:
        super().__init__(id="home-panel", **kwargs)

    def show(
        self,
        *,
        workspace: str,
        provider: str,
        model: str,
        sessions: list[tuple[str, str]] | None = None,
    ) -> None:
        recent = ""
        if sessions:
            recent = "\n".join(f"  • {sid}  {title}" for sid, title in sessions[:5])
        else:
            recent = "  • No saved sessions yet"
        self.update(
            f"[bold #a78bfa]HEX[/] [dim]CLI {__version__}[/]\n\n"
            f"[bold]Hi! How can I help you today?[/]\n\n"
            f"[dim]Workspace[/]\n  {workspace}\n\n"
            f"[dim]Model[/]\n  {provider} · {model}\n\n"
            f"[dim]Recent sessions[/]\n{recent}\n\n"
            f"[dim]Try[/]\n"
            f"  LIST .\n"
            f"  READ README.md\n"
            f"  explain this project\n\n"
            f"[dim]ctrl+p command palette · ctrl+n new session · ctrl+b sidebar[/]"
        )
