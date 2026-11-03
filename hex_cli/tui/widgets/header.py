from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Static

from hex_cli import __version__


class AppHeader(Static):
    """Compact application header."""

    def __init__(self, **kwargs) -> None:
        super().__init__(id="app-header", **kwargs)
        self._brand = "HEX"
        self._workspace = ""
        self._session = ""
        self._provider = ""
        self._model = ""
        self._status = "idle"

    def update_meta(
        self,
        *,
        workspace: str = "",
        session: str = "",
        provider: str = "",
        model: str = "",
        status: str = "idle",
    ) -> None:
        self._workspace = workspace
        self._session = session
        self._provider = provider
        self._model = model
        self._status = status
        self.refresh_content()

    def refresh_content(self) -> None:
        left = f"[bold #a78bfa]{self._brand}[/] [dim]CLI {__version__}[/]"
        mid = f"[dim]{self._workspace}[/]"
        right = f"[dim]{self._provider}[/] · {self._model} · [dim]{self._session}[/] · {self._status}"
        self.update(f"{left}  {mid}\n{right}   [dim]ctrl+p commands · ctrl+b sidebar · ctrl+n new[/]")
