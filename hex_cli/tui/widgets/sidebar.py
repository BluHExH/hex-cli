"""Collapsible left sidebar."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Label, Static


class Sidebar(Static):
    """Sessions, files, model info."""

    collapsed: reactive[bool] = reactive(False)
    provider: reactive[str] = reactive("")
    model: reactive[str] = reactive("")
    project_name: reactive[str] = reactive("")

    def __init__(self, project_root: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_root = project_root

    def compose(self) -> ComposeResult:
        with Vertical(id="sidebar"):
            yield Label("SESSIONS", classes="sidebar-title")
            yield Static("• Session 1", classes="sidebar-item -selected")
            yield Static("  (Ctrl+N new)", classes="sidebar-muted")

            yield Label("PROJECT", classes="sidebar-title")
            yield Static(f"• {self.project_root.name}", classes="sidebar-item")
            yield Static(self._short_path(str(self.project_root)), classes="sidebar-muted")

            yield Label("FILES", classes="sidebar-title")
            for name in self._list_top_files():
                yield Static(f"  {name}", classes="sidebar-item")

            yield Label("MODEL", classes="sidebar-title")
            yield Static("", id="sidebar-model", classes="sidebar-item")
            yield Static("", id="sidebar-provider", classes="sidebar-muted")

            yield Label("SHORTCUTS", classes="sidebar-title")
            yield Static("Ctrl+B  toggle sidebar", classes="sidebar-muted")
            yield Static("Ctrl+P  model / provider", classes="sidebar-muted")
            yield Static("Ctrl+H  help", classes="sidebar-muted")
            yield Static("Ctrl+L  clear chat", classes="sidebar-muted")
            yield Static("Ctrl+C  quit", classes="sidebar-muted")

    def watch_collapsed(self, value: bool) -> None:
        try:
            bar = self.query_one("#sidebar")
            bar.set_class(value, "collapsed")
            self.display = not value
        except Exception:
            self.display = not value

    def watch_model(self, value: str) -> None:
        try:
            self.query_one("#sidebar-model", Static).update(f"• {value or '—'}")
        except Exception:
            pass

    def watch_provider(self, value: str) -> None:
        try:
            self.query_one("#sidebar-provider", Static).update(f"  {value or '—'}")
        except Exception:
            pass

    def _list_top_files(self, limit: int = 8) -> list[str]:
        try:
            entries = sorted(
                self.project_root.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )
            names: list[str] = []
            for p in entries:
                if p.name.startswith(".") or p.name in ("__pycache__", "node_modules", ".venv"):
                    continue
                prefix = "📁 " if p.is_dir() else "📄 "
                names.append(prefix + p.name)
                if len(names) >= limit:
                    break
            return names or ["(empty)"]
        except Exception:
            return ["(unavailable)"]

    @staticmethod
    def _short_path(path: str, max_len: int = 24) -> str:
        if len(path) <= max_len:
            return path
        return "…" + path[-(max_len - 1) :]
