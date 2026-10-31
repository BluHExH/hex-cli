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
from hex_cli.tui.widgets.provider_dialogs import (
    ConnectProviderDialog,
    ModelBrowserDialog,
    ProvidersStatusDialog,
    SettingsDialog,
)
from hex_cli.tui.widgets.sidebar import Sidebar
from hex_cli.providers.catalog import OPENROUTER_FREE_FALLBACK, discover_models, free_models_catalog
from hex_cli.providers.credentials import (
    delete_credential,
    list_connected_provider_ids,
    mask_key,
    set_credential,
)
from hex_cli.providers.registry import list_provider_specs

# Fallback free presets (OpenRouter :free convention only — never invent paid-as-free)
FREE_MODEL_PRESETS = list(OPENROUTER_FREE_FALLBACK)


class HexApp(App[None]):
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
        model = model_override or provider_cfg.default_model
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

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

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
        """Start TUI even without an API key — show onboarding instead of exiting."""
        try:
            pcfg = self.config.get_active_provider()
            if self.config.selected_model:
                self.state.model = self.config.selected_model
            key = get_api_key(pcfg)
            self.state.connected = bool(key) or pcfg.name in ("ollama", "custom")
            # Always create provider without hard-failing on missing key
            self._provider = create_provider(
                pcfg, model=self.state.model, require_key=False
            )
            if self.state.connected:
                self._setup_agent()
                self.state.status_message = "Ready"
                self._post_system(
                    f"Connected · {pcfg.name} · {self.state.model}. "
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

    def _show_onboarding(self) -> None:
        specs = list_provider_specs()
        lines = [
            "Welcome to HEX — AI coding agent.",
            "",
            "No API key is configured yet. You can still explore the interface.",
            "",
            "Connect a provider:",
            "  /connect          interactive provider + API key setup",
            "  /models           browse models (free filter available)",
            "  /providers        list connected providers",
            "",
            "Popular options:",
        ]
        for s in specs[:6]:
            lines.append(f"  • {s.display_name}  ({s.api_key_env})")
        lines.extend(
            [
                "",
                "Free routes: use OpenRouter models ending in :free, or Ollama locally.",
                "Type /help for all commands.",
            ]
        )
        self._post_system("\n".join(lines))

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
        """Callbacks so AgentLoop can talk to the TUI instead of Rich console."""
        return {
            "print_assistant": lambda text: self.call_from_thread(
                self._post_assistant, text
            ),
            "print_tool_status": lambda name, status, detail="": self.call_from_thread(
                self._post_tool, name, status, detail
            ),
            "print_error": lambda msg: self.call_from_thread(self._post_error, msg),
            "print_warning": lambda msg: self.call_from_thread(
                self._post_status, msg
            ),
            "print_info": lambda msg: self.call_from_thread(self._post_system, msg),
            "spinner": None,  # TUI shows busy state instead
        }

    # ------------------------------------------------------------------
    # Permission bridge (worker thread → main UI)
    # ------------------------------------------------------------------

    def _ask_permission_sync(self, request: PermissionRequest) -> bool:
        """Called from agent worker thread; blocks until UI answers."""
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

    # ------------------------------------------------------------------
    # Message posting
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Chrome updates
    # ------------------------------------------------------------------

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
            busy = "● busy" if self.state.busy else "● idle"
            text = (
                f" {self.state.model}  ·  {self.state.provider_name}  ·  "
                f"{self.project_root.name}  ·  {busy}  ·  "
                f"{self.state.status_message}"
            )
            self.query_one("#footer-bar", Static).update(text)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------

    @on(PromptSubmitted)
    def handle_prompt(self, event: PromptSubmitted) -> None:
        text = event.text.strip()
        if not text:
            return
        if self.state.busy:
            self._post_status("Still working — wait for the current task to finish.")
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
        self.state.status_message = "Thinking…"
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

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_quit_app(self) -> None:
        if self.state.busy:
            self._post_status("Agent still running — press Ctrl+C again to force quit.")
            # second quit will exit
            self.state.busy = False
            return
        self.exit()

    def action_clear_chat(self) -> None:
        self.state.clear_conversation()
        if self._agent:
            # reset without Rich print
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

    def action_pick_model(self) -> None:
        self._post_status("Loading model catalog…")
        self.run_worker(self._load_and_show_models, exclusive=True, thread=True)

    def _load_and_show_models(self) -> None:
        try:
            pcfg = self.config.get_active_provider()
            models, err = discover_models(pcfg)
            if err:
                self.call_from_thread(
                    self._post_status, f"Catalog warning: {err} (using fallbacks)"
                )
            if not models:
                models = free_models_catalog()
        except Exception as e:
            self.call_from_thread(self._post_error, f"Model discovery failed: {e}")
            models = free_models_catalog()

        def _done(choice: str | None) -> None:
            if choice:
                self._set_model(choice)

        def _open() -> None:
            self.push_screen(
                ModelBrowserDialog(
                    models,
                    current=self.state.model,
                    title=f"Models — {self.state.provider_name}",
                ),
                _done,
            )

        self.call_from_thread(_open)

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

    def action_connect_provider(self) -> None:
        specs = list_provider_specs()
        connected = set(list_connected_provider_ids())

        def _done(result: tuple[str, str] | None) -> None:
            if not result:
                return
            pid, key = result
            try:
                if key:
                    set_credential(pid, key)
                self.config.active_provider = pid
                # Ensure provider entry exists
                from hex_cli.providers.registry import get_provider_spec, spec_to_config

                if pid not in self.config.providers:
                    spec = get_provider_spec(pid)
                    if spec:
                        self.config.providers[pid] = spec_to_config(spec)
                pcfg = self.config.providers[pid]
                # Export env for this process so OpenAI client sees the key
                if key:
                    import os

                    os.environ[pcfg.api_key_env] = key
                model = self.config.selected_model or pcfg.default_model
                self._provider = create_provider(pcfg, model=model, require_key=False)
                self.state.provider_name = pid
                self.state.model = model
                self.state.connected = bool(get_api_key(pcfg)) or pid in ("ollama", "custom")
                save_config(self.config)
                if self.state.connected:
                    self._setup_agent()
                    self.state.status_message = "Ready"
                    self._post_system(
                        f"Connected to {pid}. Model: {model}. "
                        f"Key: {mask_key(key or get_api_key(pcfg))}. "
                        "Type /models to browse models."
                    )
                else:
                    self._post_status(
                        f"Provider {pid} selected but no key available. "
                        "Re-run /connect with a key."
                    )
            except Exception as e:
                self._post_error(f"Connect failed: {e}")
            self._refresh_chrome()

        self.push_screen(ConnectProviderDialog(specs, connected), _done)

    def action_show_providers(self) -> None:
        lines = []
        for pid, pcfg in self.config.providers.items():
            key = get_api_key(pcfg)
            status = "connected" if key or pid in ("ollama", "custom") else "no key"
            active = " (active)" if pid == self.config.active_provider else ""
            lines.append(f"• {pid}{active} — {status} — key {mask_key(key)}")
        stored = list_connected_provider_ids()
        if stored:
            lines.append("")
            lines.append("Stored credentials: " + ", ".join(stored))
        self.push_screen(ProvidersStatusDialog(lines))

    def action_disconnect_provider(self) -> None:
        self._disconnect_named(self.state.provider_name)

    def _disconnect_named(self, name: str) -> None:
        deleted = delete_credential(name)
        if deleted:
            self._post_system(f"Removed stored key for {name}.")
        else:
            self._post_status(f"No stored key for {name} (env vars are not cleared).")
        # Re-evaluate connection
        try:
            pcfg = self.config.get_active_provider()
            key = get_api_key(pcfg)
            self.state.connected = bool(key) or pcfg.name in ("ollama", "custom")
            if not self.state.connected:
                self._agent = None
                self.state.status_message = "Not connected"
        except Exception:
            pass
        self._refresh_chrome()

    def action_show_settings(self) -> None:
        pcfg = self.config.get_active_provider()
        text = (
            f"Config: {self.config}\n".replace(str(get_api_key(pcfg) or ""), "***")
            if False
            else ""
        )
        text = (
            f"Active provider: {self.config.active_provider}\n"
            f"Model: {self.state.model}\n"
            f"Selected model (saved): {self.config.selected_model or '—'}\n"
            f"Project: {self.project_root}\n"
            f"Config dir: uses ~/.hex/\n"
            f"Credentials: ~/.hex/credentials.json\n"
            f"Max agent steps: {self.config.max_agent_steps}\n"
            f"Connected: {self.state.connected}\n"
        )
        self.push_screen(SettingsDialog(text))

    def _set_model(self, model: str) -> None:
        try:
            pcfg = self.config.get_active_provider()
            self._provider = create_provider(pcfg, model=model, require_key=False)
            self.state.model = model
            pcfg.default_model = model
            self.config.selected_model = model
            save_config(self.config)
            if self.state.connected:
                if self._agent:
                    self._agent.provider = self._provider
                else:
                    self._setup_agent()
            self._post_system(f"Model set to {model}")
        except Exception as e:
            self._post_error(str(e))
        self._refresh_chrome()

    def _set_provider(self, name: str) -> None:
        if name not in self.config.providers:
            self._post_error(
                f"Unknown provider: {name}. Use /connect to add one."
            )
            return
        try:
            self.config.active_provider = name
            save_config(self.config)
            pcfg = self.config.get_active_provider()
            model = self.config.selected_model or pcfg.default_model
            self._provider = create_provider(pcfg, model=model, require_key=False)
            self.state.provider_name = name
            self.state.model = model
            key = get_api_key(pcfg)
            self.state.connected = bool(key) or name in ("ollama", "custom")
            if self.state.connected:
                self._setup_agent()
                self.state.status_message = "Ready"
                self._post_system(f"Provider set to {name} (model {model})")
            else:
                self._agent = None
                self.state.status_message = "Not connected"
                self._post_status(
                    f"Switched to {name} but no API key. Run /connect."
                )
        except Exception as e:
            self._post_error(str(e))
            self.state.connected = False
        self._refresh_chrome()


def run_tui(project_root: Path | None = None, model: str | None = None) -> None:
    """Entry point used by the Typer CLI."""
    root = (project_root or Path.cwd()).resolve()
    load_dotenv_if_present(root)
    config = load_config()
    app = HexApp(root, config, model_override=model)
    app.run()
