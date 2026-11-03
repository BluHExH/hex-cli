from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Input, RichLog, Static

from hex_cli import __version__
from hex_cli.agent.runner import AgentRunner
from hex_cli.changes.tracker import ChangeLog
from hex_cli.config.settings import HexSettings, load_settings
from hex_cli.permissions.gate import PermissionGate
from hex_cli.providers.base import ChatMessage
from hex_cli.providers.factory import create_provider
from hex_cli.sessions.store import Session, SessionStore
from hex_cli.tools.registry import ToolRegistry


class HexApp(App[None]):
    """Minimal professional coding-agent TUI — HEX branded."""

    CSS = """
    Screen { background: #0d1117; }
    #chat { height: 1fr; border: solid #30363d; padding: 0 1; }
    #status { height: 1; color: #8b949e; background: #010409; padding: 0 1; }
    #input { dock: bottom; height: 3; border: solid #a78bfa; }
    #sidebar { width: 22; border: solid #30363d; padding: 0 1; }
    """

    BINDINGS = [
        Binding("ctrl+n", "new_session", "New"),
        Binding("ctrl+c", "quit", "Quit"),
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

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal():
            yield Static(
                f"[bold #a78bfa]HEX[/]\n[dim]v{__version__}[/]\n\nSessions\n• {self.session.id}",
                id="sidebar",
            )
            with Vertical():
                yield RichLog(id="chat", markup=True, wrap=True, highlight=True)
                yield Static(self._status_line(), id="status")
                yield Input(placeholder="Message HEX…  (Enter to send)", id="input")
        yield Footer()

    def on_mount(self) -> None:
        chat = self.query_one("#chat", RichLog)
        chat.write("[bold]Hi! How can I help you today?[/]")
        chat.write("[dim]Powered by HEX · NeonBuild · type a task or READ path/to/file[/]")
        self.query_one("#input", Input).focus()

    def _status_line(self) -> str:
        return (
            f" {self.settings.provider} · {self.settings.model} · "
            f"{self.workspace.name} · session {self.session.id} · HEX {__version__}"
        )

    def action_new_session(self) -> None:
        self.session = self.store.create(title="New session")
        self.history.clear()
        chat = self.query_one("#chat", RichLog)
        chat.clear()
        chat.write("[bold]New session.[/] Hi! How can I help you today?")
        self.query_one("#status", Static).update(self._status_line())

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        if not text:
            return
        chat = self.query_one("#chat", RichLog)
        chat.write(f"[bold cyan]You[/]\n{text}")
        try:
            result = self.runner.run_turn(self.history, text)
            self.history = [m for m in result.messages if m.role in {"user", "assistant", "tool", "system"}]
            for ev in result.tool_events:
                status = "ok" if ev["ok"] else "err"
                chat.write(f"[yellow]tool:{ev['tool']}[/] ({status})")
                detail = ev["output"] or ev["error"]
                if detail:
                    chat.write(f"[dim]{detail[:800]}[/]")
            chat.write(f"[bold #a78bfa]HEX[/]\n{result.assistant_text}")
            # persist
            self.session.messages = [
                {"role": m.role, "content": m.content} for m in self.history if m.role in {"user", "assistant"}
            ]
            self.store.save(self.session)
        except Exception as exc:  # noqa: BLE001
            chat.write(f"[red]Error:[/] {exc}")
