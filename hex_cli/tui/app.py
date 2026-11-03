from __future__ import annotations

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
from hex_cli.tui.widgets.home import HomeScreen
from hex_cli.tui.widgets.palette import CommandPalette
from hex_cli.tui.widgets.sidebar import SessionSidebar
from hex_cli.tui.widgets.status import StatusBar
from hex_cli.tui.widgets.timeline import ConversationTimeline


class HexApp(App[None]):
    """HEX CLI 2.1 professional coding-agent TUI."""

    CSS = HEX_THEME_CSS
    TITLE = f"HEX CLI {__version__}"

    BINDINGS = [
        Binding("ctrl+n", "new_session", "New", show=True),
        Binding("ctrl+b", "toggle_sidebar", "Sidebar", show=True),
        Binding("ctrl+p", "command_palette", "Palette", show=True),
        Binding("ctrl+l", "focus_composer", "Composer", show=False),
        Binding("ctrl+c", "cancel_or_quit", "Cancel", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("question_mark", "show_help", "Help", show=False),
    ]

    def __init__(self, workspace: Path | None = None) -> None:
        super().__init__()
        self.workspace = (workspace or Path.cwd()).resolve()
        self.settings = load_settings(self.workspace)
        self.settings.workspace = str(self.workspace)
        self.store = SessionStore(self.workspace)
        self.session: Session = self.store.create(title="Main")
        self.history: list[ChatMessage] = []
        self.changes = ChangeLog()
        gate = PermissionGate(mode=self.settings.permission_mode)
        self.tools = ToolRegistry(self.workspace, gate)
        self.provider = create_provider(self.settings)
        self.runner = AgentRunner(self.provider, self.tools, self.settings, self.changes)
        self._busy = False
        self._show_home = True

    def compose(self) -> ComposeResult:
        yield AppHeader()
        with Horizontal(id="main-row"):
            yield SessionSidebar()
            with Vertical(id="content-col"):
                yield HomeScreen()
                yield ConversationTimeline()
                with Vertical(id="composer-wrap"):
                    yield PromptComposer()
        yield StatusBar()

    def on_mount(self) -> None:
        self._refresh_chrome()
        self.query_one(ConversationTimeline).display = False
        self.query_one(HomeScreen).show(
            workspace=str(self.workspace),
            provider=self.settings.provider,
            model=self.settings.model,
            sessions=self._session_pairs(),
        )
        self.query_one(PromptComposer).focus()
        self._adapt_layout()

    def on_resize(self, event) -> None:  # noqa: ANN001
        self._adapt_layout()

    def _adapt_layout(self) -> None:
        """Hide sidebar on narrow terminals."""
        sidebar = self.query_one(SessionSidebar)
        if self.size.width < 100:
            sidebar.display = False
        elif not sidebar._collapsed:
            sidebar.display = True

    def _session_pairs(self) -> list[tuple[str, str]]:
        return [(s.id, s.title) for s in self.store.list()[:8]]

    def _refresh_chrome(self) -> None:
        status = "working" if self._busy else "idle"
        self.query_one(AppHeader).update_meta(
            workspace=self.workspace.name,
            session=self.session.id,
            provider=self.settings.provider,
            model=self.settings.model,
            status=status,
        )
        self.query_one(SessionSidebar).set_content(
            session_id=self.session.id,
            session_title=self.session.title,
            workspace=str(self.workspace),
            provider=self.settings.provider,
            model=self.settings.model,
            permission_mode=self.settings.permission_mode,
            change_count=len(self.changes.items),
            sessions=self._session_pairs(),
        )
        self.query_one(StatusBar).set_status(
            state=status,
            model=f"{self.settings.provider}/{self.settings.model}",
            session=self.session.id,
            workspace=self.workspace.name,
        )

    def _ensure_conversation_view(self) -> None:
        if self._show_home:
            self._show_home = False
            self.query_one(HomeScreen).display = False
            self.query_one(ConversationTimeline).display = True

    def action_new_session(self) -> None:
        if self._busy:
            return
        self.session = self.store.create(title="New session")
        self.history.clear()
        self.changes = ChangeLog()
        self.runner.changes = self.changes
        timeline = self.query_one(ConversationTimeline)
        timeline.clear()
        self._show_home = True
        self.query_one(HomeScreen).display = True
        self.query_one(HomeScreen).show(
            workspace=str(self.workspace),
            provider=self.settings.provider,
            model=self.settings.model,
            sessions=self._session_pairs(),
        )
        timeline.display = False
        self._refresh_chrome()
        self.query_one(PromptComposer).focus()

    def action_toggle_sidebar(self) -> None:
        self.query_one(SessionSidebar).toggle()
        self._adapt_layout()

    def action_focus_composer(self) -> None:
        self.query_one(PromptComposer).focus()

    def action_command_palette(self) -> None:
        def _done(cmd: str | None) -> None:
            if not cmd:
                return
            actions = {
                "new_session": self.action_new_session,
                "toggle_sidebar": self.action_toggle_sidebar,
                "focus_composer": self.action_focus_composer,
                "cancel": self.action_cancel_or_quit,
                "help": self.action_show_help,
                "quit": self.action_quit,
            }
            fn = actions.get(cmd)
            if fn:
                fn()

        self.push_screen(CommandPalette(), _done)

    def action_show_help(self) -> None:
        timeline = self.query_one(ConversationTimeline)
        self._ensure_conversation_view()
        timeline.add_system(
            "Shortcuts: Ctrl+Enter send · Ctrl+N new · Ctrl+B sidebar · "
            "Ctrl+P palette · Ctrl+C cancel · Ctrl+Q quit · Ctrl+L composer"
        )

    def action_cancel_or_quit(self) -> None:
        if self._busy:
            self.runner.request_cancel()
            self.query_one(ConversationTimeline).add_system("Cancel requested…")
            return
        self.exit()

    def on_prompt_composer_submitted(self, event: PromptComposer.Submitted) -> None:
        text = event.text.strip()
        if not text or self._busy:
            return
        self._ensure_conversation_view()
        timeline = self.query_one(ConversationTimeline)
        timeline.add_user(text)
        self._busy = True
        self.query_one(PromptComposer).set_busy(True)
        self._refresh_chrome()
        self.run_worker(self._run_turn(text), exclusive=True, thread=True)

    def _run_turn(self, text: str) -> None:
        try:
            result = self.runner.run_turn(self.history, text)
            self.call_from_thread(self._apply_result, result)
        except Exception as exc:  # noqa: BLE001
            self.call_from_thread(self._apply_error, str(exc))

    def _apply_result(self, result) -> None:
        timeline = self.query_one(ConversationTimeline)
        self.history = [m for m in result.messages if m.role in {"user", "assistant", "tool", "system"}]
        for ev in result.tool_events:
            timeline.add_tool(ev["tool"], bool(ev["ok"]), ev.get("output") or ev.get("error") or "")
        timeline.add_assistant(result.assistant_text, cancelled=bool(result.cancelled))
        if not self.session.title or self.session.title in {"Main", "New session"}:
            self.session.title = result.messages[0].content[:40] if result.messages else self.session.title
        self.session.messages = [
            {"role": m.role, "content": m.content} for m in self.history if m.role in {"user", "assistant"}
        ]
        try:
            self.store.save(self.session)
        except OSError as exc:
            timeline.add_error(f"Session save failed: {exc}")
        self._busy = False
        self.query_one(PromptComposer).set_busy(False)
        self._refresh_chrome()
        self.query_one(PromptComposer).focus()

    def _apply_error(self, message: str) -> None:
        self.query_one(ConversationTimeline).add_error(message)
        self._busy = False
        self.query_one(PromptComposer).set_busy(False)
        self._refresh_chrome()
        self.query_one(PromptComposer).focus()
