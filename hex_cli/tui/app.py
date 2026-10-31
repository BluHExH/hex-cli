"""HEX full-screen TUI application (Textual)."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Static

from hex_cli import __version__
from hex_cli.agent.loop import AgentLoop
from hex_cli.config import (
    AppConfig,
    get_api_key,
    load_config,
    load_dotenv_if_present,
    save_config,
)
from hex_cli.permissions import PermissionManager, PermissionRequest
from hex_cli.providers.base import create_provider
from hex_cli.tui.state import SessionState
from hex_cli.tui.theme import HEX_CSS
from hex_cli.tui.widgets.chat import ChatLog
from hex_cli.tui.widgets.dialogs import HelpDialog, PermissionDialog, SelectDialog
from hex_cli.tui.widgets.header import HeaderBar
from hex_cli.tui.widgets.input_panel import InputPanel, PromptSubmitted
from hex_cli.tui.widgets.sidebar import Sidebar
from hex_cli.tui.stage2_mixin import Stage2Mixin
from hex_cli.providers.catalog import OPENROUTER_FREE_FALLBACK

FREE_MODEL_PRESETS = list(OPENROUTER_FREE_FALLBACK)


class HexApp(Stage2Mixin, App[None]):
    """OpenCode-inspired full-screen coding agent UI."""

    CSS = HEX_CSS
    TITLE = f"HEX CLI v{__version__}"
    BINDINGS = [
        Binding("ctrl+c", "quit_app", "Quit", priority=True),
        Binding("ctrl+q", "quit_app", "Quit"),
        Binding("ctrl+l", "clear_chat", "Clear"),
        Binding("ctrl+n", "new_session", "New"),
        Binding("ctrl+p", "pick_model", "Model"),
        Binding("ctrl+b", "toggle_sidebar", "Sidebar"),
        Binding("ctrl+h", "show_help", "Help"),
        Binding("escape", "focus_input", "Focus", show=False),
    ]

    def __init__(
        self,
        project_root: Path,
        config: AppConfig,
        model_override: str | None = None,
    ) -> None:
        super().__init__()
        self.project_root = project_root.resolve()
        self.config = config
        provider_cfg = config.get_active_provider()
        model = model_override or getattr(config, "selected_model", None) or provider_cfg.default_model
        self.state = SessionState(
            project_root=self.project_root,
            provider_name=provider_cfg.name,
            model=model,
        )
        self._provider = None
        self._agent: AgentLoop | None = None
        self._perm_event = threading.Event()
        self._perm_result = False
        self._ui_lock = threading.Lock()

    def compose(self) -> ComposeResult:
        yield HeaderBar()
        with Horizontal():
            yield Sidebar(self.project_root)
            with Vertical(id="chat-container"):
                yield ChatLog()
                yield InputPanel()
        yield Static("", id="footer-bar")

    def on_mount(self) -> None:
        self._refresh_chrome()
        self.query_one(InputPanel).focus_input()
        self.set_interval(0.5, self._tick_footer)
        self.call_later(self._boot_provider)

    def _boot_provider(self) -> None:
        """Start TUI even without an API key."""
        try:
            pcfg = self.config.get_active_provider()
            if getattr(self.config, "selected_model", None):
                self.state.model = self.config.selected_model
            key = get_api_key(pcfg)
            self.state.connected = bool(key) or pcfg.name in ("ollama", "custom")
            self._provider = create_provider(
                pcfg, model=self.state.model, require_key=False
            )
            if self.state.connected:
                self._setup_agent()
                self.state.status_message = "Ready"
                self._post_system(
                    f"Connected \u00b7 {pcfg.name} \u00b7 {self.state.model}. "
                    "Describe a coding task, or type /models to switch models."
                )
            else:
                self._agent = None
                self.state.status_message = "Not connected"
                self._show_onboarding()
        except Exception as e:
            self.state.connected = False
            self._agent = None
            self.state.status_message = "Provider error"
            self._post_error(str(e))
            self._show_onboarding()
        self._refresh_chrome()

    def _setup_agent(self) -> None:
        assert self._provider is not None
        pm = PermissionManager(self.config, self.project_root)
        pm.set_ask_callback(self._ask_permission_sync)
        self._agent = AgentLoop(
            self.project_root,
            self._provider,
            self.config,
            pm,
            ui_hooks=self._ui_hooks(),
        )

    def _ui_hooks(self) -> dict[str, Any]:
        return {
            "print_assistant": lambda text: self.call_from_thread(self._post_assistant, text),
            "print_tool_status": lambda name, status, detail="": self.call_from_thread(
                self._post_tool, name, status, detail
            ),
            "print_error": lambda msg: self.call_from_thread(self._post_error, msg),
            "print_warning": lambda msg: self.call_from_thread(self._post_status, msg),
            "print_info": lambda msg: self.call_from_thread(self._post_system, msg),
            "spinner": None,
        }

    def _ask_permission_sync(self, request: PermissionRequest) -> bool:
        self._perm_event.clear()
        self._perm_result = False
        self.call_from_thread(self._show_permission_dialog, request)
        self._perm_event.wait(timeout=300)
        return self._perm_result

    def _show_permission_dialog(self, request: PermissionRequest) -> None:
        def _done(result: bool | None) -> None:
            self._perm_result = bool(result)
            self._perm_event.set()

        self.push_screen(
            PermissionDialog(
                action=request.action.value,
                description=request.description,
                path=request.path or "",
                detail=request.detail or "",
                high_impact=request.high_impact,
            ),
            _done,
        )

    def _post_user(self, text: str) -> None:
        e = self.state.add("user", text)
        self.query_one(ChatLog).append_entry(e)

    def _post_assistant(self, text: str) -> None:
        if not text:
            return
        e = self.state.add("assistant", text)
        self.query_one(ChatLog).append_entry(e)

    def _post_tool(self, name: str, status: str, detail: str = "") -> None:
        line = name if not detail else f"{name}  {detail}"
        e = self.state.add("tool", line, status=status)
        self.query_one(ChatLog).append_entry(e)

    def _post_error(self, text: str) -> None:
        e = self.state.add("error", text)
        self.query_one(ChatLog).append_entry(e)

    def _post_system(self, text: str) -> None:
        e = self.state.add("system", text)
        self.query_one(ChatLog).append_entry(e)

    def _post_status(self, text: str) -> None:
        e = self.state.add("status", text)
        self.query_one(ChatLog).append_entry(e)

    def _refresh_chrome(self) -> None:
        try:
            header = self.query_one(HeaderBar)
            header.project = str(self.project_root)
            header.provider = self.state.provider_name
            header.model = self.state.model
            header.connected = self.state.connected
            header.status = self.state.status_message
            side = self.query_one(Sidebar)
            side.provider = self.state.provider_name
            side.model = self.state.model
            side.collapsed = not self.state.sidebar_visible
        except Exception:
            pass
        self._tick_footer()

    def _tick_footer(self) -> None:
        try:
            busy = "\u25cf busy" if self.state.busy else "\u25cf idle"
            text = (
                f" {self.state.model}  \u00b7  {self.state.provider_name}  \u00b7  "
                f"{self.project_root.name}  \u00b7  {busy}  \u00b7  "
                f"{self.state.status_message}"
            )
            self.query_one("#footer-bar", Static).update(text)
        except Exception:
            pass

    @on(PromptSubmitted)
    def handle_prompt(self, event: PromptSubmitted) -> None:
        text = event.text.strip()
        if not text:
            return
        if self.state.busy:
            self._post_status("Still working \u2014 wait for the current task to finish.")
            return

        lower = text.lower().strip()
        if lower in ("/exit", "/quit", "exit", "quit"):
            self.exit()
            return
        if lower in ("/help", "help"):
            self.action_show_help()
            return
        if lower == "/clear":
            self.action_clear_chat()
            return
        if lower == "/status":
            self._post_system(
                f"Project: {self.project_root}\n"
                f"Provider: {self.state.provider_name}\n"
                f"Model: {self.state.model}\n"
                f"Connected: {self.state.connected}"
            )
            return
        if lower in ("/connect", "/connect provider"):
            self.action_connect_provider()
            return
        if lower in ("/models", "/model"):
            self.action_pick_model()
            return
        if lower.startswith("/model "):
            self._set_model(text.split(maxsplit=1)[1].strip())
            return
        if lower in ("/providers", "/provider"):
            self.action_show_providers()
            return
        if lower.startswith("/provider "):
            self._set_provider(text.split(maxsplit=1)[1].strip())
            return
        if lower in ("/disconnect",):
            self.action_disconnect_provider()
            return
        if lower.startswith("/disconnect "):
            self._disconnect_named(text.split(maxsplit=1)[1].strip())
            return
        if lower in ("/settings",):
            self.action_show_settings()
            return

        if not self.state.connected or self._agent is None:
            self._post_status(
                "Not connected. Run /connect to add a provider, then try again."
            )
            return

        self._post_user(text)
        self.run_agent_task(text)

    @work(thread=True)
    def run_agent_task(self, text: str) -> None:
        self.state.busy = True
        self.state.status_message = "Thinking\u2026"
        self.call_from_thread(self._refresh_chrome)
        try:
            if self._agent is None:
                self.call_from_thread(self._post_error, "Agent not ready. Check provider config.")
                return
            self._agent.run(text)
            self.state.status_message = "Ready"
        except Exception as e:
            self.call_from_thread(self._post_error, f"Agent error: {e}")
            self.state.status_message = "Error"
        finally:
            self.state.busy = False
            self.call_from_thread(self._refresh_chrome)
            self.call_from_thread(lambda: self.query_one(InputPanel).focus_input())

    def action_quit_app(self) -> None:
        if self.state.busy:
            self._post_status("Agent still running \u2014 press Ctrl+C again to force quit.")
            self.state.busy = False
            return
        self.exit()

    def action_clear_chat(self) -> None:
        self.state.clear_conversation()
        if self._agent:
            self._agent._init_system()
        self.query_one(ChatLog).clear_messages()
        self._refresh_chrome()

    def action_new_session(self) -> None:
        self.action_clear_chat()
        self._post_system("New session started.")

    def action_toggle_sidebar(self) -> None:
        self.state.sidebar_visible = not self.state.sidebar_visible
        self._refresh_chrome()

    def action_show_help(self) -> None:
        self.push_screen(HelpDialog())

    def action_focus_input(self) -> None:
        self.query_one(InputPanel).focus_input()

    def action_pick_provider(self) -> None:
        options = list(self.config.providers.keys())

        def _done(choice: str | None) -> None:
            if choice:
                self._set_provider(choice)

        self.push_screen(
            SelectDialog(
                "Select provider",
                options,
                current=self.state.provider_name,
            ),
            _done,
        )


def run_tui(project_root: Path | None = None, model: str | None = None) -> None:
    """Entry point used by the Typer CLI."""
    root = (project_root or Path.cwd()).resolve()
    load_dotenv_if_present(root)
    config = load_config()
    app = HexApp(root, config, model_override=model)
    app.run()
