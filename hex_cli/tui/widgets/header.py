"""Top header bar for HEX TUI."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Static


class HeaderBar(Static):
    """HEX branding + project + provider + connection status."""

    project: reactive[str] = reactive("")
    provider: reactive[str] = reactive("")
    model: reactive[str] = reactive("")
    status: reactive[str] = reactive("Ready")
    connected: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        with Horizontal(id="header"):
            yield Static(" ◆ HEX ", id="header-brand")
            yield Static("", id="header-project")
            yield Static("", id="header-provider")
            yield Static("○ offline", id="header-status", classes="status-err")

    def watch_project(self, value: str) -> None:
        try:
            name = value.replace("\\", "/").rstrip("/").split("/")[-1] if value else ""
            self.query_one("#header-project", Static).update(f"  {name}")
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
                w.update("● online")
                w.set_classes("status-ok")
            else:
                w.update("○ offline")
                w.set_classes("status-err")
        except Exception:
            pass

    def _refresh_provider(self) -> None:
        try:
            model = self.model
            if len(model) > 36:
                model = model[:33] + "…"
            label = f"{self.provider} · {model}" if model else self.provider
            self.query_one("#header-provider", Static).update(label)
        except Exception:
            pass
