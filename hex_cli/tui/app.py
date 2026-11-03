from __future__ import annotations

from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from hex_cli import __version__
from hex_cli.agent.runner import AgentRunner
from hex_cli.changes.tracker import ChangeLog
from hex_cli.config.settings import load_settings
from hex_cli.permissions.gate import PermissionGate
from hex_cli.providers.base import ChatMessage
from hex_cli.providers.factory import create_provider
from hex_cli.sessions.store import Session, SessionStore
from hex_cli.tools.registry import ToolRegistry
from hex_cli.tui.theme import HEX_THEME_CSS
from hex_cli.tui.widgets.composer import PromptComposer
from hex_cli.tui.widgets.header import AppHeader
from hex_cli.tui.widgets.left_rail import LeftRail
from hex_cli.tui.widgets.palette import CommandPalette
from hex_cli.tui.widgets.right_rail import RightRail
from hex_cli.tui.widgets.status import StatusBar
from hex_cli.tui.widgets.timeline import ConversationTimeline


class HexApp(App[None]):
    """Three-column HEX coding workspace (OpenCode-structure layout, HEX brand)."""

    CSS = HEX_THEME_CSS
    TITLE = f"HEX CLI {__version__}"

    BINDINGS = [
        Binding("ctrl+n", "new_session", "New", show=True),
        Binding("ctrl+b", "toggle_left", "Left", show=True),
        Binding("ctrl+l", "toggle_right", "Right", show=True),
        Binding("ctrl+p", "palette", "Palette", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("escape", "cancel_or_idle", "Cancel", show=True),
    ]

    def __init__(self, workspace: Path | None = None) -> None:
        super().__init__()
        self.workspace = (workspace or Path.cwd()).resolve()
        self.settings = load_settings(self.workspace)
        self.settings.workspace = str(self.workspace)
        self.store = SessionStore(self.workspace)
        self.session: Session = self.store.create(title="Session 1")
        self.history: list[ChatMessage] = []
        self.changes = ChangeLog()
        gate = PermissionGate(mode=self.settings.permission_mode)
        self.tools = ToolRegistry(self.workspace, gate)
        self.provider = create_provider(self.settings)
        self.runner = AgentRunner(self.provider, self.tools, self.settings, self.changes)
        self._busy = False
        self._started = datetime.now()
        self._activities: list[tuple[str, str, bool]] = []
        self._ctx_chars = 0

    def compose(self) -> ComposeResult:
        yield AppHeader()
        with Horizontal(id="body"):
            yield LeftRail()
            with Vertical(id="center"):
                yield Static(f"  Session 1   +", id="session-tabs")
                yield ConversationTimeline()
                yield PromptComposer()
            yield RightRail()
        yield StatusBar()

    def on_mount(self) -> None:
        self.query_one(ConversationTimeline).show_welcome(
            f"{self.settings.provider}/{self.settings.model}"
        )
        self._refresh_all()
        self.query_one(PromptComposer).set_permission_label(self.settings.permission_mode)
        self.query_one(PromptComposer).focus_input()
        self._adapt()

    def on_resize(self, event) -> None:  # noqa: ANN001
        self._adapt()

    def _adapt(self) -> None:
        left = self.query_one(LeftRail)
        right = self.query_one(RightRail)
        w = self.size.width
        if w < 90:
            left.display = False
            right.display = False
        elif w < 120:
            left.display = not left._collapsed
            right.display = False
        else:
            left.display = not left._collapsed
            right.display = not right._collapsed

    def _recent_files(self) -> list[str]:
        files: list[str] = []
        try:
            for p in sorted(self.workspace.rglob("*")):
                if p.is_file() and not any(part.startswith(".") for part in p.parts):
                    files.append(str(p.relative_to(self.workspace)))
                if len(files) >= 6:
                    break
        except OSError:
            pass
        return files

    def _change_rows(self) -> list[tuple[str, str]]:
        rows: list[tuple[str, str]] = []
        for c in self.changes.items[-12:]:
            before_len = len(c.before or "")
            after_len = len(c.after or "")
            delta = after_len - before_len
            sign = f"+{delta}" if delta >= 0 else str(delta)
            rows.append((c.path, sign))
        return rows

    def _refresh_all(self) -> None:
        model = f"{self.settings.provider}/{self.settings.model}"
        self.query_one(AppHeader).set_meta(
            workspace=str(self.workspace),
            model=self.settings.model,
            provider=self.settings.provider,
            agent_status="Working" if self._busy else "Agent",
        )
        self.query_one(LeftRail).set_data(
            workspace=str(self.workspace),
            context_chars=self._ctx_chars,
            context_max=self.settings.context_max_chars,
            tool_count=len(self.tools.schemas()),
            permission_mode=self.settings.permission_mode,
            recent_files=self._recent_files(),
        )
        elapsed = datetime.now() - self._started
        mins, secs = divmod(int(elapsed.total_seconds()), 60)
        self.query_one(RightRail).set_data(
            changes=self._change_rows(),
            activities=list(self._activities[-12:]),
            model=model,
            context_line=f"{self._ctx_chars // 1000}K / {self.settings.context_max_chars // 1000}K",
            started=self._started.strftime("%H:%M"),
            duration=f"{mins}m {secs}s",
            auto_save=True,
        )
        self.query_one(StatusBar).set_status(
            ready=not self._busy,
            model=model,
            workspace=str(self.workspace),
        )
        tabs = self.query_one("#session-tabs", Static)
        tabs.update(f"  [reverse] {self.session.title or 'Session 1'}  × [/]  [dim]+[/]")

    def action_new_session(self) -> None:
        if self._busy:
            return
        self.session = self.store.create(title="Session")
        self.history.clear()
        self.changes = ChangeLog()
        self.runner.changes = self.changes
        self._activities.clear()
        self._ctx_chars = 0
        self._started = datetime.now()
        tl = self.query_one(ConversationTimeline)
        tl.clear()
        tl.show_welcome(f"{self.settings.provider}/{self.settings.model}")
        self._refresh_all()
        self.query_one(PromptComposer).focus_input()

    def action_toggle_left(self) -> None:
        self.query_one(LeftRail).toggle()
        self._adapt()

    def action_toggle_right(self) -> None:
        self.query_one(RightRail).toggle()
        self._adapt()

    def action_palette(self) -> None:
        def done(cmd: str | None) -> None:
            if not cmd:
                return
            {
                "new_session": self.action_new_session,
                "toggle_left": self.action_toggle_left,
                "toggle_right": self.action_toggle_right,
                "focus_composer": lambda: self.query_one(PromptComposer).focus_input(),
                "cancel": self.action_cancel_or_idle,
                "quit": self.action_quit,
            }.get(cmd, lambda: None)()

        self.push_screen(CommandPalette(), done)

    def action_cancel_or_idle(self) -> None:
        if self._busy:
            self.runner.request_cancel()
            self.query_one(ConversationTimeline).add_system("Cancel requested…")

    def on_prompt_composer_submitted(self, event: PromptComposer.Submitted) -> None:
        text = event.text.strip()
        if not text or self._busy:
            return
        now = datetime.now().strftime("%-I:%M %p") if hasattr(datetime, "strftime") else ""
        try:
            now = datetime.now().strftime("%H:%M")
        except Exception:
            now = ""
        tl = self.query_one(ConversationTimeline)
        tl.add_user(text, now)
        self._busy = True
        self.query_one(PromptComposer).set_busy(True)
        self._refresh_all()
        self.run_worker(lambda: self._run_turn(text), exclusive=True, thread=True)

    def _run_turn(self, text: str) -> None:
        try:
            result = self.runner.run_turn(self.history, text)
            self.call_from_thread(self._apply_result, result)
        except Exception as exc:  # noqa: BLE001
            self.call_from_thread(self._apply_error, str(exc))

    def _apply_result(self, result) -> None:
        tl = self.query_one(ConversationTimeline)
        self.history = [m for m in result.messages if m.role in {"user", "assistant", "tool", "system"}]
        self._ctx_chars = sum(len(m.content) for m in self.history)
        for ev in result.tool_events:
            name = ev["tool"]
            ok = bool(ev["ok"])
            detail = (ev.get("output") or ev.get("error") or "")[:400]
            kind = {
                "read_file": "Read",
                "write_file": "Edit",
                "run_shell": "Terminal",
                "list_dir": "List",
                "search_files": "Search",
            }.get(name, name)
            self._activities.append((kind, "done" if ok else "err", ok))
            tl.add_tool_card(kind, name, ok, preview=detail)
        now = datetime.now().strftime("%H:%M")
        if result.tool_events and not result.cancelled:
            tl.add_planning(len(result.tool_events), "Tool steps completed.")
        tl.add_assistant(result.assistant_text, now, cancelled=bool(result.cancelled))
        if result.assistant_text and not result.cancelled:
            # light success cue when tools ran
            if result.tool_events and all(e["ok"] for e in result.tool_events):
                tl.add_success("Turn completed.")
        self.session.messages = [
            {"role": m.role, "content": m.content} for m in self.history if m.role in {"user", "assistant"}
        ]
        if self.session.title in {"Session", "Session 1", "Main", "New session"} and self.history:
            for m in self.history:
                if m.role == "user":
                    self.session.title = m.content[:48]
                    break
        try:
            self.store.save(self.session)
        except OSError as exc:
            tl.add_error(f"save failed: {exc}")
        self._busy = False
        self.query_one(PromptComposer).set_busy(False)
        self._refresh_all()
        self.query_one(PromptComposer).focus_input()

    def _apply_error(self, message: str) -> None:
        self.query_one(ConversationTimeline).add_error(message)
        self._busy = False
        self.query_one(PromptComposer).set_busy(False)
        self._refresh_all()
        self.query_one(PromptComposer).focus_input()
