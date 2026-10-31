"""OpenCode-style left sidebar — brand, sessions, project, agent, model, git."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button, Static


class SessionSelected(Message):
    def __init__(self, session_id: str) -> None:
        super().__init__()
        self.session_id = session_id


class NewSessionRequested(Message):
    pass


class AgentClicked(Message):
    pass


class ModelClicked(Message):
    pass



class Sidebar(Vertical):
    """Persistent left rail."""

    provider: reactive[str] = reactive("")
    model: reactive[str] = reactive("")
    agent: reactive[str] = reactive("general")
    collapsed: reactive[bool] = reactive(False)
    connected: reactive[bool] = reactive(False)
    git_branch: reactive[str] = reactive("")

    def __init__(self, project_root: Path, **kwargs) -> None:
        super().__init__(id="sidebar", **kwargs)
        self.project_root = project_root
        self._session_rows: list[tuple[str, str, bool]] = []

    def compose(self) -> ComposeResult:
        yield Static("  ⬡  HEX", id="sidebar-brand")
        yield Static("SESSIONS", classes="sidebar-section")
        yield VerticalScroll(id="session-list")
        yield Button("+  New session", id="btn-new-session")
        with Vertical(id="sidebar-footer"):
            yield Static("PROJECT", classes="sidebar-section")
            yield Static(f"  {self.project_root.name}", classes="sidebar-meta", id="sidebar-project")
            yield Static(
                f"  {self._short_path(self.project_root)}",
                classes="sidebar-path",
                id="sidebar-path",
            )
            yield Static("AGENT", classes="sidebar-section")
            yield Static("  general", classes="sidebar-meta", id="sidebar-agent")
            yield Static("MODEL", classes="sidebar-section")
            yield Static("  —", classes="sidebar-meta", id="sidebar-model")
            yield Static("PROVIDER", classes="sidebar-section")
            yield Static("  —", classes="sidebar-meta", id="sidebar-provider")
            yield Static("GIT", classes="sidebar-section")
            yield Static("  —", classes="sidebar-meta", id="sidebar-git")
            yield Static("STATUS", classes="sidebar-section")
            yield Static("  ○ offline", classes="sidebar-meta", id="sidebar-conn")

    @staticmethod
    def _short_path(p: Path, max_len: int = 24) -> str:
        s = str(p)
        if len(s) <= max_len:
            return s
        return "…" + s[-(max_len - 1) :]

    def watch_collapsed(self, value: bool) -> None:
        self.set_class(value, "collapsed")

    def watch_provider(self, value: str) -> None:
        try:
            self.query_one("#sidebar-provider", Static).update(f"  {value or '—'}")
        except Exception:
            pass

    def watch_model(self, value: str) -> None:
        try:
            model = value or "—"
            if len(model) > 26:
                model = model[:23] + "…"
            self.query_one("#sidebar-model", Static).update(f"  {model}")
        except Exception:
            pass

    def watch_agent(self, value: str) -> None:
        try:
            self.query_one("#sidebar-agent", Static).update(f"  {value or 'general'}")
        except Exception:
            pass

    def watch_connected(self, value: bool) -> None:
        try:
            label = "  ● online" if value else "  ○ offline"
            self.query_one("#sidebar-conn", Static).update(label)
        except Exception:
            pass

    def watch_git_branch(self, value: str) -> None:
        try:
            self.query_one("#sidebar-git", Static).update(f"  {value or '—'}")
        except Exception:
            pass

    def set_sessions(self, rows: list[tuple[str, str, bool]]) -> None:
        self._session_rows = rows
        try:
            container = self.query_one("#session-list", VerticalScroll)
            container.remove_children()
            for sid, name, active in rows:
                cls = "sidebar-item -active" if active else "sidebar-item"
                marker = "▸ " if active else "  "
                container.mount(
                    Static(f"{marker}{name}", classes=cls, id=f"sess-{sid}")
                )
        except Exception:
            pass

    def on_click(self, event) -> None:  # noqa: ANN001
        try:
            wid = getattr(event.widget, "id", None) or ""
            if not isinstance(wid, str):
                return
            if wid.startswith("sess-"):
                self.post_message(SessionSelected(wid[5:]))
            elif wid == "sidebar-agent":
                self.post_message(AgentClicked())
            elif wid == "sidebar-model":
                self.post_message(ModelClicked())
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-new-session":
            self.post_message(NewSessionRequested())
