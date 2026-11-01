"""Top header bar for HEX TUI — minimal OpenCode-like chrome."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Static


class HeaderBar(Static):
    """Thin top strip: brand + short connection hint."""

    project: reactive[str] = reactive("")
    provider: reactive[str] = reactive("")
    model: reactive[str] = reactive("")
    status: reactive[str] = reactive("Ready")
    connected: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        with Horizontal(id="header"):
            yield Static(" HEX ", id="header-brand")
            yield Static("", id="header-project")
            yield Static("", id="header-provider")
            yield Static("", id="header-status")

    def watch_project(self, value: str) -> None:
        # Path shown in footer (OpenCode-style); keep header quiet
        try:
            self.query_one("#header-project", Static).update("")
        except Exception:
            pass

    def watch_provider(self, value: str) -> None:
        self._refresh_provider()

    def watch_model(self, value: str) -> None:
        self._refresh_provider()

    def watch_status(self, value: str) -> None:
        pass

    def watch_connected(self, value: bool) -> None:
        try:
            w = self.query_one("#header-status", Static)
            if value:
                w.update("")
            else:
                w.update(" offline — /provider")
                w.set_classes("status-err")
        except Exception:
            pass

    def _refresh_provider(self) -> None:
        # Model lives in footer status line
        try:
            self.query_one("#header-provider", Static).update("")
        except Exception:
            pass
