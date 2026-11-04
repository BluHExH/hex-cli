from __future__ import annotations

from datetime import datetime  # noqa: F401  (clock helpers in notes)
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical

from hex_cli import __version__
from hex_cli.agent.runner import AgentRunner
from hex_cli.changes.tracker import ChangeLog
from hex_cli.config.settings import load_settings, save_settings
from hex_cli.context.compact import compact_messages
from hex_cli.permissions.gate import PermissionDecision, PermissionGate, PermissionRequest
from hex_cli.providers.base import ChatMessage
from hex_cli.providers.factory import create_provider
from hex_cli.sessions.store import Session, SessionStore
from hex_cli.tools.registry import ToolRegistry
from hex_cli.tui.commands import resolve as resolve_command
from hex_cli.tui.theme import HEX_THEME_CSS
from hex_cli.tui.widgets.composer import PromptComposer
from hex_cli.tui.widgets.dialogs import CommandDialog, ModelsDialog, SessionsDialog
from hex_cli.tui.widgets.header import AppHeader
from hex_cli.tui.widgets.status import StatusBar
from hex_cli.tui.widgets.timeline import ConversationTimeline, tool_label


class _PlanGate:
    """Read-only gate wrapper mirroring OpenCode's Plan agent (denies writes/shell)."""

    def __init__(self, inner: PermissionGate) -> None:
        self._inner = inner

    @property
    def mode(self) -> str:  # pragma: no cover - pass-through
        return self._inner.mode

    def decide(self, req: PermissionRequest) -> PermissionDecision:
        if req.action in {"write", "shell"}:
            return PermissionDecision.DENY
        return self._inner.decide(req)


class HexApp(App[None]):
    """OpenCode-style terminal AI coding agent (HEX brand, real backend pipeline)."""

    CSS = HEX_THEME_CSS
    TITLE = f"HEX CLI {__version__}"

    BINDINGS = [
        Binding("tab", "cycle_mode", "Agents", show=False),
        Binding("ctrl+n", "command('new')", "New session", show=False),
        Binding("ctrl+s", "command('sessions')", "Sessions", show=False),
        Binding("ctrl+m", "command('models')", "Models", show=False),
        Binding("ctrl+u", "command('undo')", "Undo", show=False),
        Binding("ctrl+p", "palette", "Commands", show=True),
        Binding("ctrl+k", "palette", "Commands", show=False),
        Binding("ctrl+q", "command('exit')", "Quit", show=False),
        Binding("escape", "interrupt", "Interrupt", show=True),
    ]

    def __init__(self, workspace: Path | None = None) -> None:
        super().__init__()
        self.workspace = (workspace or Path.cwd()).resolve()
        self.settings = load_settings(self.workspace)
        self.settings.workspace = str(self.workspace)
        self.store = SessionStore(self.workspace)
        self.session: Session = self.store.create(title="New session")
        self.history: list[ChatMessage] = []
        self.changes = ChangeLog()
        self._base_gate = PermissionGate(mode=self.settings.permission_mode)
        self.tools = ToolRegistry(self.workspace, self._base_gate)
        self.provider = create_provider(self.settings)
        self.runner = AgentRunner(self.provider, self.tools, self.settings, self.changes)
        self._busy = False
        self._details = True
        self._agent_mode = "build"
        self._ctx_chars = 0

    # -- layout ----------------------------------------------------------
    def compose(self) -> ComposeResult:
        yield AppHeader()
        with Vertical(id="body"):
            yield ConversationTimeline()
            yield PromptComposer()
        yield StatusBar()

    def on_mount(self) -> None:
        self.query_one(PromptComposer).set_model(self.settings.provider, self.settings.model)
        self.query_one(ConversationTimeline).reset(
            "Type a message, / for commands, ! for shell â€” Tab cycles agent mode."
        )
        self._refresh_all()
        self.query_one(PromptComposer).focus_input()

    @property
    def composer(self) -> PromptComposer:
        return self.query_one(PromptComposer)

    @property
    def timeline(self) -> ConversationTimeline:
        return self.query_one(ConversationTimeline)

    # -- header/status ---------------------------------------------------
    def _refresh_all(self, *_: object) -> None:
        tokens = self._ctx_chars // 4
        pct = min(100, round(self._ctx_chars / max(1, self.settings.context_max_chars) * 100))
        self.query_one(AppHeader).set_meta(
            title=self.session.title,
            tokens=tokens,
            pct=pct,
            cost="$0.00",
        )
        self.composer.set_model(self.settings.provider, self.settings.model)
        self.composer.set_mode(self._agent_mode)
        self.query_one(StatusBar).set_status(ready=not self._busy)

    # -- bindings --------------------------------------------------------
    def action_cycle_mode(self) -> None:
        self._agent_mode = "plan" if self._agent_mode == "build" else "build"
        self.tools.gate = _PlanGate(self._base_gate) if self._agent_mode == "plan" else self._base_gate
        self.timeline.add_note(f"Agent mode: {'Plan (read-only)' if self._agent_mode == 'plan' else 'Build'}")
        self._refresh_all()

    def action_palette(self) -> None:
        def done(cmd: str | None) -> None:
            if cmd:
                self.run_command(cmd.lstrip("/"))

        self.push_screen(CommandDialog(), done)

    def action_interrupt(self) -> None:
        if self._busy:
            self.runner.request_cancel()
            self.timeline.add_note("Interrupt requestedâ€¦")

    def action_command(self, name: str) -> None:
        self.run_command(name)

    # -- commands --------------------------------------------------------
    def run_command(self, name: str) -> None:
        """Execute a resolved canonical slash command."""
        if self._busy and name not in {"exit"}:
            self.timeline.add_note(f"/{name} ignored while a turn is running.")
            return
        {
            "new": self._cmd_new,
            "sessions": self._cmd_sessions,
            "models": self._cmd_models,
            "undo": self._cmd_undo,
            "compact": self._cmd_compact,
            "details": self._cmd_details,
            "help": self._cmd_help,
            "exit": self._cmd_exit,
        }.get(name, lambda: None)()

    def _cmd_new(self) -> None:
        self.session = self.store.create(title="New session")
        self.history = []
        self._ctx_chars = 0
        self.timeline.reset("New session â€” type a message, / for commands, ! for shell.")
        self._refresh_all()
        self.composer.focus_input()

    def _cmd_sessions(self) -> None:
        rows: list[tuple[str, str, str]] = []
        for s in self.store.list():
            stamp = s.updated_at.replace("T", " ").split(".")[0][:16]
            rows.append((s.title or s.id, stamp, s.id))
        if not rows:
            self.timeline.add_note("No saved sessions.")
            return

        def done(sid: str | None) -> None:
            if not sid:
                return
            self._load_session(sid)

        self.push_screen(SessionsDialog(rows), done)

    def _load_session(self, sid: str) -> None:
        try:
            loaded = self.store.load(sid)
        except (OSError, ValueError) as exc:
            self.timeline.add_error(f"session load failed: {exc}")
            return
        self.session = loaded
        self.history = [ChatMessage(role=m["role"], content=m["content"]) for m in loaded.messages]
        self._ctx_chars = sum(len(m.content) for m in self.history)
        self.timeline.replay(self.history, details=self._details)
        self._refresh_all()
        self.composer.focus_input()

    def _cmd_models(self) -> None:
        current = f"{self.settings.provider}/{self.settings.model}"
        rows: list[tuple[str, bool]] = [
            (current, True),
            ("edit .hex/config.json to add providers", False),
        ]

        def done(_label: str | None) -> None:
            if _label and _label != current:
                self.timeline.add_note(f"Provider {_label} selected.")

        self.push_screen(ModelsDialog(rows), done)

    def _cmd_undo(self) -> None:
        """Remove the most recent user message and everything after it."""
        idx = next((i for i in range(len(self.history) - 1, -1, -1) if self.history[i].role == "user"), None)
        if idx is None:
            self.timeline.add_note("Nothing to undo.")
            return
        self.history = self.history[:idx]
        self.session.messages = [
            {"role": m.role, "content": m.content} for m in self.history if m.role in {"user", "assistant"}
        ]
        try:
            self.store.save(self.session)
        except OSError as exc:
            self.timeline.add_error(f"save failed: {exc}")
        self._ctx_chars = sum(len(m.content) for m in self.history)
        self.timeline.replay(self.history, details=self._details)
        self.timeline.add_note(f"Undone â€” {idx} message(s) removed.")
        self._refresh_all()

    def _cmd_compact(self) -> None:
        if not self.history:
            self.timeline.add_note("Nothing to compact.")
            return
        compacted = compact_messages(self.history, self.settings.context_max_chars // 4)
        self.history = compacted
        self._ctx_chars = sum(len(m.content) for m in self.history)
        self.timeline.replay(self.history, details=self._details)
        self.timeline.add_note("Context compacted.")
        self._refresh_all()

    def _cmd_details(self) -> None:
        self._details = not self._details
        self.timeline.replay(self.history, details=self._details)
        self.timeline.add_note(f"Tool details {'shown' if self._details else 'hidden'}.")

    def _cmd_help(self) -> None:
        self.push_screen(CommandDialog())

    def _cmd_exit(self) -> None:
        self.exit()

    # -- turn plumbing ---------------------------------------------------
    def on_prompt_composer_submitted(self, event: PromptComposer.Submitted) -> None:
        text = event.text.strip()
        if not text or self._busy:
            return
        cmd, rest = resolve_command(text)
        if cmd is not None:
            if cmd == "exit":
                self._cmd_exit()
                return
            if cmd in {"help", "sessions", "models"}:
                self.run_command(cmd)
                return
            if rest:
                self.timeline.add_note(f"/{cmd} takes no arguments.")
                return
            self.run_command(cmd)
            return
        if text.startswith("!"):
            self._start_shell(text[1:].strip())
            return
        self.timeline.add_user(text)
        self._busy = True
        self.composer.set_busy(True)
        self._refresh_all()
        self.run_worker(lambda: self._run_turn(text), exclusive=True, thread=True)

    def _start_shell(self, command: str) -> None:
        if not command:
            self.timeline.add_note("Empty shell command.")
            return
        self.timeline.add_user(f"!{command}")
        self._busy = True
        self.composer.set_busy(True)
        self._refresh_all()
        self.run_worker(lambda: self._run_shell(command), exclusive=True, thread=True)

    def _run_shell(self, command: str) -> None:
        self.runner.reset_cancel()
        result = self.tools.execute("run_shell", {"command": command})
        self.call_from_thread(self._apply_shell, command, result)

    def _apply_shell(self, command: str, result) -> None:
        ok = bool(result.ok)
        out = result.output if ok else result.error
        self.timeline.add_tool("run_shell", ok, out=out.rstrip() or "(no output)", meta={"command": command})
        self.history.append(ChatMessage(role="user", content=f"!{command}"))
        self.history.append(
            ChatMessage(role="tool", content=out or "(no output)", name="run_shell", tool_call_id="shell", meta={"command": command})
        )
        self.history.append(ChatMessage(role="assistant", content="Shell command captured."))
        self._post_turn_common()

    def _run_turn(self, text: str) -> None:
        try:
            result = self.runner.run_turn(self.history, text)
            self.call_from_thread(self._apply_result, result)
        except Exception as exc:  # noqa: BLE001
            self.call_from_thread(self._apply_error, str(exc))

    def _apply_result(self, result) -> None:
        self.history = [m for m in result.messages if m.role in {"user", "assistant", "tool", "system"}]
        self._ctx_chars = sum(len(m.content) for m in self.history)
        for ev in result.tool_events:
            ok = bool(ev["ok"])
            out = ev.get("output") if ok else (ev.get("error") or ev.get("output") or "")
            self.timeline.add_tool(
                ev["tool"], ok, duration=ev.get("duration"), out=out, meta=dict(ev.get("args") or {})
            )
        self.timeline.add_assistant(result.assistant_text, cancelled=bool(result.cancelled))
        self._persist_session()
        self._post_turn_common()

    def _apply_error(self, message: str) -> None:
        self.timeline.add_error(message)
        self._post_turn_common()

    def _post_turn_common(self) -> None:
        self._busy = False
        self.composer.set_busy(False)
        self._refresh_all()
        self.composer.focus_input()

    def _persist_session(self) -> None:
        self.session.messages = [
            {"role": m.role, "content": m.content} for m in self.history if m.role in {"user", "assistant"}
        ]
        if self.session.title == "New session" and self.history:
            for m in self.history:
                if m.role == "user":
                    self.session.title = m.content.strip()[:48]
                    break
        try:
            self.store.save(self.session)
        except OSError as exc:
            self.timeline.add_error(f"save failed: {exc}")
        self.session.metadata["tool_labels"] = [tool_label(m.name or "") for m in self.history if m.role == "tool"]
