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
from hex_cli.tui.theme import HEX_CSS, HEX_LOGO
from hex_cli.tui.widgets.chat import ChatLog
from hex_cli.tui.widgets.dialogs import HelpDialog, PermissionDialog, SelectDialog
from hex_cli.tui.widgets.header import HeaderBar
from hex_cli.tui.widgets.input_panel import InputPanel, PromptSubmitted
from hex_cli.tui.widgets.activity_bar import ActivityBar
from hex_cli.tui.widgets.diff_review import (
    DiffAccept,
    DiffReject,
    DiffReviewClosed,
    DiffReviewPanel,
)
from hex_cli.tui.widgets.command_palette import CommandPalette
from hex_cli.tui.widgets.file_picker import FilePicker
from hex_cli.tui.widgets.provider_dialogs import (
    ConnectProviderDialog,
    ModelBrowserDialog,
    ProvidersStatusDialog,
    SettingsDialog,
)
from hex_cli.tui.widgets.sidebar import (
    AgentClicked,
    ModelClicked,
    NewSessionRequested,
    SessionSelected,
    Sidebar,
)
from hex_cli.tui.stage2_mixin import Stage2Mixin
from hex_cli.providers.catalog import OPENROUTER_FREE_FALLBACK, discover_models, free_models_catalog
from hex_cli.providers.credentials import (
    delete_credential,
    list_connected_provider_ids,
    mask_key,
    set_credential,
)
from hex_cli.providers.registry import list_provider_specs
from hex_cli.knowledge.identity import try_offline_identity

# Fallback free presets (OpenRouter :free convention only — never invent paid-as-free)
FREE_MODEL_PRESETS = list(OPENROUTER_FREE_FALLBACK)


class HexApp(Stage2Mixin, App[None]):
    """OpenCode-inspired full-screen coding agent UI."""

    CSS = HEX_CSS
    TITLE = f"HEX CLI v{__version__}"
    BINDINGS = [
        ("ctrl+shift+c", "copy_code", "Copy code"),
        Binding("ctrl+c", "quit_app", "Quit", priority=True),
        Binding("ctrl+q", "quit_app", "Quit"),
        Binding("ctrl+l", "clear_chat", "Clear"),
        Binding("ctrl+n", "new_session", "New"),
        Binding("ctrl+p", "command_palette", "Palette"),
        Binding("ctrl+period", "stop_agent", "Stop", show=False),
        Binding("ctrl+f", "file_picker", "Files", show=False),
        Binding("ctrl+e", "external_editor", "Editor", show=False),
        Binding("ctrl+y", "redo_change", "Redo", show=False),
        Binding("ctrl+b", "toggle_sidebar", "Sidebar"),
        Binding("ctrl+h", "show_help", "Help"),
        Binding("ctrl+shift+a", "cycle_agent", "Agent", show=False),
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

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield HeaderBar()
        with Horizontal():
            yield Sidebar(self.project_root)
            with Vertical(id="chat-container"):
                yield ChatLog()
                yield ActivityBar()
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
                self._show_banner()
                self.state.status_message = "Ready"
                # Conversation stays clean; status is in footer/header only
            else:
                self._agent = None
                self.state.status_message = "Not connected"
                self._show_banner()
                self._show_onboarding()
        except Exception as e:
            self.state.connected = False
            self._agent = None
            self.state.status_message = "Provider error"
            self._post_error(str(e))
            self._show_banner()
            self._show_onboarding()
        self._refresh_sessions_sidebar()
        self._refresh_chrome()

    def _show_onboarding(self) -> None:
        # Minimal: leave welcome widget in ChatLog; one short status line only
        self.state.status_message = "Not connected — /connect"
        self._refresh_chrome()


    def _show_banner(self) -> None:
        # Branding lives in header/sidebar only — do not spam the conversation
        return


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
            "print_tool_status": lambda name, status, detail="", output="", error="": self.call_from_thread(
                self._post_tool, name, status, detail, output, error
            ),
            "print_error": lambda msg: self.call_from_thread(self._post_error, msg),
            "print_warning": lambda msg: self.call_from_thread(
                self._post_status, msg
            ),
            "print_info": lambda msg: self.call_from_thread(self._post_system, msg),
            "spinner": None,
            "on_stream_start": lambda: self.call_from_thread(self._stream_start),
            "on_stream_token": lambda t: self.call_from_thread(self._stream_token, t),
            "on_stream_end": lambda: self.call_from_thread(self._stream_end),
            "on_busy": lambda b: self.call_from_thread(self._set_busy_ui, b),
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


    def _stream_start(self) -> None:
        self._stream_id = None
        self._stream_buf = ""
        try:
            self._stream_id = self.query_one(ChatLog).begin_assistant_stream()
        except Exception:
            self._stream_id = None
        try:
            self.query_one(ActivityBar).set_activity("thinking", busy=True)
        except Exception:
            pass

    def _stream_token(self, token: str) -> None:
        self._stream_buf = getattr(self, "_stream_buf", "") + token
        wid = getattr(self, "_stream_id", None)
        if wid:
            try:
                self.query_one(ChatLog).update_message(wid, self._stream_buf, kind="assistant")
            except Exception:
                pass

    def _stream_end(self) -> None:
        buf = getattr(self, "_stream_buf", "")
        if buf:
            self.state.add("assistant", buf)
        self._stream_id = None
        self._stream_buf = ""

    def _set_busy_ui(self, busy: bool) -> None:
        self.state.busy = busy
        try:
            self.query_one(InputPanel).set_busy(busy)
        except Exception:
            pass
        try:
            bar = self.query_one(ActivityBar)
            if busy:
                bar.set_activity("thinking", busy=True)
            else:
                bar.set_activity("completed", busy=False)
                # auto-hide after brief moment
                self.set_timer(1.2, lambda: bar.set_activity("idle", busy=False))
        except Exception:
            pass
        self._refresh_chrome()


    def _post_user(self, text: str) -> None:
        e = self.state.add("user", text)
        self.query_one(ChatLog).append_entry(e)

    def _post_assistant(self, text: str) -> None:
        if not text:
            return
        e = self.state.add("assistant", text)
        self.query_one(ChatLog).append_entry(e)

    def _post_tool(self, name: str, status: str, detail: str = "", output: str = "", error: str = "") -> None:
        line = name if not detail else f"{name}  {detail}"
        e = self.state.add("tool", line, status=status)
        try:
            self.query_one(ChatLog).append_tool_card(name, status, detail, output=output, error=error)
        except Exception:
            self.query_one(ChatLog).append_entry(e)
        try:
            phase = name if status == "running" else ("completed" if status in ("ok", "completed") else status)
            self.query_one(ActivityBar).set_activity(
                name if status == "running" else phase,
                busy=status == "running" or self.state.busy,
                detail=detail or "",
            )
        except Exception:
            pass


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
            side.connected = self.state.connected
            side.collapsed = not self.state.sidebar_visible
        except Exception:
            pass
        self._tick_footer()
        try:
            sidebar = self.query_one(Sidebar)
            sidebar.agent = getattr(self.state, "agent", "general")
        except Exception:
            pass
        try:
            panel = self.query_one(InputPanel)
            panel.set_meta(
                agent=getattr(self.state, "agent", "general"),
                model=self.state.model,
            )
        except Exception:
            pass
        try:
            from hex_cli.tools.git_tools import GitTools
            from hex_cli.permissions import PermissionManager
            gt = GitTools(self.project_root, PermissionManager(self.config, self.project_root), self.config)
            st = gt.git_status()
            if st.get("ok"):
                self.query_one(Sidebar).git_branch = st.get("branch", "")
        except Exception:
            pass

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


        # OpenCode-style: leading ! runs a shell command into the conversation
        if text.startswith("!") and not text.startswith("!/"):
            cmd = text[1:].strip()
            if not cmd:
                self._post_status("Usage: ! <shell command>")
                return
            self._post_user(text)
            self._run_bang_command(cmd)
            return

        # Offline identity (no network) — only for natural language questions
        if not text.startswith("/"):
            offline = try_offline_identity(text)
            if offline:
                self._post_user(text)
                self._post_assistant(offline)
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
        if lower in ("/new", "/session new"):
            self.action_new_session()
            return
        if lower in ("/sessions", "/session"):
            rows = self.state.session_names()
            lines = [f"{'*' if a else ' '} {n} ({i})" for i, n, a in rows]
            self._post_system("Sessions:\n" + "\n".join(lines) if lines else "No sessions.")
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
        if lower in ("/plan",) or lower.startswith("/plan "):
            rest = text.split(maxsplit=1)
            if self._agent:
                self._agent.set_agent("plan")
                self.state.agent = "plan"
                self.state.active_session.agent = "plan"
            if len(rest) == 2:
                self._post_user(rest[1])
                self.run_agent_task(rest[1], plan_only=True)
            else:
                self._post_status("Switched to Plan agent. Usage: /plan <task>")
            return
        if lower in ("/build",) or lower.startswith("/build "):
            rest = text.split(maxsplit=1)
            if self._agent:
                self._agent.set_agent("build")
                self.state.agent = "build"
                self.state.active_session.agent = "build"
            if len(rest) == 2:
                self._post_user(rest[1])
                self.run_agent_task(rest[1], plan_only=False)
            else:
                self._post_status("Switched to Build agent. Usage: /build <task>")
            return
        if lower in ("/explore",) or lower.startswith("/explore "):
            rest = text.split(maxsplit=1)
            if self._agent:
                self._agent.set_agent("explore")
                self.state.agent = "explore"
                self.state.active_session.agent = "explore"
            if len(rest) == 2:
                self._post_user(rest[1])
                self.run_agent_task(rest[1], plan_only=False)
            else:
                self._post_status("Switched to Explore agent. Usage: /explore <query>")
            return
        if lower in ("/agent", "/agents"):
            from hex_cli.agents import list_agents
            lines = []
            for a in list_agents():
                mark = "*" if a.id == getattr(self.state, "agent", "general") else " "
                lines.append(f"{mark} {a.display_name} ({a.id}) — {a.description}")
            self._post_system("Agents:\n" + "\n".join(lines) + "\n\nSwitch: /agent <build|plan|explore|general>")
            return
        if lower.startswith("/agent "):
            name = text.split(maxsplit=1)[1].strip().lower()
            try:
                if self._agent:
                    profile = self._agent.set_agent(name)
                    self.state.agent = profile.id
                    self.state.active_session.agent = profile.id
                    self._post_system(f"Active agent: {profile.display_name} — {profile.description}")
                else:
                    self.state.agent = name
                    self._post_system(f"Agent set to {name} (will apply when agent starts)")
            except Exception as e:
                self._post_error(f"Unknown agent: {name} ({e})")
            return
        if lower in ("/save", "/session save"):
            pid = self.state.persist_active()
            self._post_system(f"Session saved (id={pid})")
            return
        if lower.startswith("/session rename "):
            new_name = text.split(maxsplit=2)[2] if len(text.split(maxsplit=2)) > 2 else ""
            if new_name and self.state.rename_session(self.state.active_session_id, new_name):
                self._post_system(f"Renamed to: {new_name}")
                self._refresh_sessions_sidebar()
            else:
                self._post_status("Usage: /session rename <name>")
            return
        if lower in ("/session delete",):
            sid = self.state.active_session_id
            if self.state.delete_session(sid):
                self._post_system("Session deleted.")
                self._refresh_sessions_sidebar()
                self.action_clear_chat()
            return
        if lower.startswith("/session search ") or lower.startswith("/history "):
            q = text.split(maxsplit=2)[-1] if " " in text else ""
            hits = self.state.search_persistent(q)
            if not hits:
                self._post_status("No matching sessions.")
            else:
                lines = [f"• {h.name} [{h.agent}] {h.id[:8]} msgs={h.message_count}" for h in hits[:20]]
                self._post_system("Search results:\n" + "\n".join(lines))
            return
        if lower in ("/history",):
            hits = self.state.list_persistent()
            if not hits:
                self._post_status("No saved sessions for this project.")
            else:
                lines = [f"• {h.name} [{h.agent}] id={h.id[:8]} msgs={h.message_count}" for h in hits[:20]]
                self._post_system("Saved sessions:\n" + "\n".join(lines))
            return

        if lower in ("/mcp", "/mcp list"):
            from hex_cli.mcp.client import MCPClient
            client = getattr(self, "_mcp", None)
            if client is None:
                self._mcp = MCPClient()
                client = self._mcp
            servers = client.list_servers()
            if not servers:
                self._post_status("No MCP servers connected. Use /mcp connect <name> -- <command...>")
            else:
                lines = [f"• {s['name']} connected={s['connected']} tools={s['tools']}" for s in servers]
                self._post_system("MCP servers:\n" + "\n".join(lines))
            return
        if lower in ("/mcp tools",):
            client = getattr(self, "_mcp", None) or MCPClient()
            tools = client.list_tools()
            if not tools:
                self._post_status("No MCP tools available.")
            else:
                lines = [f"• {t.namespaced_name} — {t.description[:60]}" for t in tools]
                self._post_system("MCP tools:\n" + "\n".join(lines))
            return
        if lower.startswith("/mcp connect "):
            # /mcp connect name -- cmd arg1 arg2
            rest = text[len("/mcp connect "):].strip()
            if " -- " not in rest:
                self._post_status("Usage: /mcp connect <name> -- <command> [args...]")
                return
            name, _, cmd_s = rest.partition(" -- ")
            import shlex
            from hex_cli.mcp.client import MCPClient, MCPServerConfig
            if not hasattr(self, "_mcp") or self._mcp is None:
                self._mcp = MCPClient()
            cfg = MCPServerConfig(name=name.strip(), command=shlex.split(cmd_s.strip()))
            result = self._mcp.connect(cfg)
            if result.get("ok"):
                self._post_system(f"MCP connected: {name} ({result.get('tools')} tools)")
            else:
                self._post_error(result.get("error", "connect failed"))
            return
        if lower.startswith("/mcp disconnect "):
            name = text.split(maxsplit=2)[-1]
            client = getattr(self, "_mcp", None)
            if client and client.disconnect(name):
                self._post_system(f"Disconnected MCP server: {name}")
            else:
                self._post_status(f"Server not connected: {name}")
            return
        if lower in ("/skills", "/skills list"):
            from hex_cli.skills.loader import SkillLoader
            loader = SkillLoader(self.project_root)
            loader.reload()
            skills = loader.list_skills()
            if not skills:
                self._post_status("No skills found in ~/.hex/skills or .hex/skills")
            else:
                lines = [f"• {s.name} [{s.source}] — {s.description[:60]}" for s in skills]
                self._post_system("Skills:\n" + "\n".join(lines))
            return
        if lower.startswith("/skills show "):
            name = text.split(maxsplit=2)[-1]
            from hex_cli.skills.loader import SkillLoader
            loader = SkillLoader(self.project_root)
            loader.reload()
            s = loader.get(name)
            if not s:
                self._post_status(f"Skill not found: {name}")
            else:
                self._post_system(f"# {s.name}\n{s.description}\n\n{s.instructions[:3000]}")
            return
        if lower in ("/skills reload",):
            from hex_cli.skills.loader import SkillLoader
            n = SkillLoader(self.project_root).reload()
            self._post_system(f"Reloaded {n} skill(s)")
            return
        if lower in ("/worktree", "/worktree list"):
            from hex_cli.worktree.manager import WorktreeManager
            from hex_cli.permissions import PermissionManager
            wt = WorktreeManager(self.project_root, PermissionManager(self.config, self.project_root))
            result = wt.list_worktrees()
            if not result.get("ok"):
                self._post_error(result.get("error", "worktree list failed"))
            else:
                lines = [f"• {t.get('path')} [{t.get('branch', t.get('head', '?'))}]" for t in result.get("worktrees", [])]
                self._post_system("Worktrees:\n" + ("\n".join(lines) if lines else "(none)"))
            return
        if lower in ("/lsp",):
            from hex_cli.lsp.client import LSPClient
            client = getattr(self, "_lsp", None)
            if client is None:
                self._lsp = LSPClient(self.project_root)
                client = self._lsp
            available = client.available_defaults()
            sessions = client.list_sessions()
            lines = [f"Available: {', '.join(available) or '(none found on PATH)'}"]
            if sessions:
                lines += [f"Session: {s['language']} init={s['initialized']}" for s in sessions]
            self._post_system("LSP:\n" + "\n".join(lines))
            return

        if lower.startswith("/theme"):
            parts = text.split(maxsplit=1)
            if len(parts) == 2:
                self.action_set_theme(parts[1].strip())
            else:
                self._show_themes()
            return
        if lower in ("/redo",):
            self.action_redo_change()
            return
        if lower in ("/files", "/file"):
            self.action_file_picker()
            return
        if lower in ("/editor",):
            self.action_external_editor()
            return
        if lower in ("/export",):
            self._export_conversation()
            return
        if lower in ("/compact", "/summarize"):
            self._compact_session()
            return
        if lower in ("/diff", "/review"):
            self.action_open_diff_review()
            return
        if lower in ("/undo",):
            if self._agent:
                result = self._agent.changes.undo_last()
                if result.get("ok"):
                    self._post_system(f"Undo: {result.get('restored')} ({result.get('action')})")
                else:
                    self._post_error(result.get("error", "undo failed"))
            else:
                self._post_status("Agent not ready.")
            return
        if lower in ("/tools",):
            if self._agent:
                lines = [f"• {t['name']} [{t['risk']}] — {t['description']}" for t in self._agent.tools_list()]
                self._post_system("Tools:\n" + "\n".join(lines))
            else:
                from hex_cli.tools.registry import list_tools_for_display
                lines = [f"• {t['name']} [{t['risk']}] — {t['description']}" for t in list_tools_for_display()]
                self._post_system("Tools:\n" + "\n".join(lines))
            return
        if lower in ("/permissions",):
            p = self.config.permissions
            self._post_system(
                "Permission modes:\n"
                f"  read_files={p.read_files}\n"
                f"  create_files={p.create_files}\n"
                f"  modify_files={p.modify_files}\n"
                f"  delete_files={p.delete_files}\n"
                f"  run_commands={p.run_commands}\n"
                f"  git_commit={p.git_commit}\n"
                f"  git_push={p.git_push}"
            )
            return
        if lower in ("/init",):
            from hex_cli.tools.project import ProjectTools
            from hex_cli.permissions import PermissionManager
            pm = PermissionManager(self.config, self.project_root)
            pt = ProjectTools(self.project_root, pm, self.config)
            overview = pt.project_overview()
            self._post_system(
                "Project init:\n" + str(overview)
            )
            return

        if not self.state.connected or self._agent is None:
            self._post_status(
                "Not connected. Run /connect to add a provider, then try again."
            )
            return

        # Custom slash commands
        if text.startswith("/"):
            from hex_cli.commands_ext.loader import CommandLoader
            loader = CommandLoader(self.project_root)
            loader.reload()
            parts = text[1:].split(maxsplit=1)
            cmd_name = parts[0].lower()
            cmd_args = parts[1] if len(parts) > 1 else ""
            custom = loader.get(cmd_name)
            if custom:
                rendered = custom.render(cmd_args)
                if custom.agent and self._agent:
                    try:
                        self._agent.set_agent(custom.agent)
                        self.state.agent = custom.agent
                    except Exception:
                        pass
                self._post_user(f"/{cmd_name} {cmd_args}".strip())
                self._post_system(f"Custom command /{cmd_name} → agent")
                self.run_agent_task(rendered)
                return

        self._post_user(text)
        self.run_agent_task(self._expand_at_files(text))

    @work(thread=True)
    def run_agent_task(self, text: str, plan_only: bool = False) -> None:
        self.state.busy = True
        self.state.status_message = "Thinking…"
        self.call_from_thread(self._set_busy_ui, True)
        try:
            if self._agent is None:
                self.call_from_thread(self._post_error, "Agent not ready. Check provider config.")
                return
            self._agent.run(text, plan_only=plan_only)
            self.state.status_message = "Ready"
        except Exception as e:
            self.call_from_thread(self._post_error, f"Agent error: {e}")
            self.state.status_message = "Error"
        finally:
            self.state.busy = False
            self.call_from_thread(self._set_busy_ui, False)
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
            try:
                self._agent._init_system()
            except Exception:
                pass
        self.query_one(ChatLog).clear_messages(
            banner="[dim]Conversation cleared. Ask HEX something…[/dim]"
        )
        self._refresh_chrome()
        self.query_one(InputPanel).focus_input()

    def action_new_session(self) -> None:
        session = self.state.new_session()
        if self._agent:
            try:
                self._agent._init_system()
            except Exception:
                pass
        self.query_one(ChatLog).clear_messages(
            banner=(
                f"[bold #c084fc]{session.name}[/]\n"
                "[dim]New session ready. Describe a coding task or type / for commands.[/]"
            )
        )
        self._refresh_sessions_sidebar()
        self._refresh_chrome()
        self.query_one(InputPanel).focus_input()

    def _refresh_sessions_sidebar(self) -> None:
        try:
            side = self.query_one(Sidebar)
            side.set_sessions(self.state.session_names())
        except Exception:
            pass

    @on(NewSessionRequested)
    
    def on_agent_clicked(self, event: AgentClicked) -> None:
        self.action_cycle_agent()

    def on_model_clicked(self, event: ModelClicked) -> None:
        self.action_pick_model()

    def on_new_session_requested(self, _event: NewSessionRequested) -> None:
        self.action_new_session()

    @on(SessionSelected)
    def on_session_selected(self, event: SessionSelected) -> None:
        if not self.state.switch_session(event.session_id):
            return
        # Rebuild chat from stored entries
        log = self.query_one(ChatLog)
        log.clear_messages(banner="")
        # remove empty welcome if we have entries
        entries = list(self.state.entries)
        if not entries:
            log.clear_messages()
        else:
            try:
                log.remove_children()
                log._has_welcome = False
            except Exception:
                pass
            for e in entries:
                log.append_entry(e)
        self._refresh_sessions_sidebar()
        self._refresh_chrome()

    def action_toggle_sidebar(self) -> None:
        self.state.sidebar_visible = not self.state.sidebar_visible
        self._refresh_chrome()

    def action_show_help(self) -> None:
        self.push_screen(HelpDialog())

    
    def action_cycle_agent(self) -> None:
        order = ["general", "build", "plan", "explore"]
        cur = getattr(self.state, "agent", "general")
        try:
            idx = order.index(cur)
        except ValueError:
            idx = 0
        nxt = order[(idx + 1) % len(order)]
        self.state.agent = nxt
        self.state.active_session.agent = nxt
        if self._agent:
            try:
                self._agent.set_agent(nxt)
            except Exception:
                pass
        self._post_system(f"Agent: {nxt}")
        self._refresh_chrome()



    def _run_bang_command(self, command: str) -> None:
        """Execute !command via CommandTools (permission-gated)."""
        try:
            from hex_cli.tools.commands import CommandTools
            from hex_cli.permissions import PermissionManager
            pm = PermissionManager(self.config, self.project_root)
            try:
                pm.set_ask_callback(lambda req: self._ask_permission_sync(req))
            except Exception:
                pass
            tools = CommandTools(self.project_root, pm, self.config)
            self._post_tool("run_command", "running", command[:80])
            result = tools.run_command(command)
            if result.get("skipped"):
                self._post_tool("run_command", "skipped", str(result.get("error", "denied"))[:80])
            elif result.get("ok"):
                out = (result.get("stdout") or result.get("output") or "")[:4000]
                self._post_tool("run_command", "ok", f"exit {result.get('exit_code', 0)}")
                if out:
                    self._post_system(out)
            else:
                self._post_tool("run_command", "error", str(result.get("error", "failed"))[:80])
                err = result.get("stderr") or result.get("error") or ""
                if err:
                    self._post_error(str(err)[:2000])
        except Exception as exc:
            self._post_error(f"!command failed: {exc}")

    def _expand_at_files(self, text: str) -> str:
        """Expand @path references by appending file contents (read-only, size-capped)."""
        import re
        refs = re.findall(r"@([\w./\\-]+)", text)
        if not refs:
            return text
        extras = []
        for ref in refs[:8]:
            path = (self.project_root / ref).resolve()
            try:
                path.relative_to(self.project_root.resolve())
            except ValueError:
                extras.append(f"[skipped {ref}: outside project]")
                continue
            if not path.is_file():
                extras.append(f"[skipped {ref}: not a file]")
                continue
            try:
                raw = path.read_text(encoding="utf-8", errors="replace")
                if len(raw) > 12000:
                    raw = raw[:12000] + "\n…(truncated)"
                extras.append(f"--- file: {ref} ---\n{raw}")
            except OSError as e:
                extras.append(f"[skipped {ref}: {e}]")
        if not extras:
            return text
        return text + "\n\n" + "\n\n".join(extras)



    def action_file_picker(self) -> None:
        def _done(path: str | None) -> None:
            if not path:
                return
            try:
                ta = self.query_one("#prompt-input")
                cur = getattr(ta, "text", "") or ""
                insert = f"@{path} "
                if hasattr(ta, "insert"):
                    ta.insert(insert)
                elif hasattr(ta, "load_text"):
                    ta.load_text((cur + " " + insert).strip() + " ")
                self.query_one(InputPanel).focus_input()
            except Exception as e:
                self._post_error(f"Could not insert @{path}: {e}")
        self.push_screen(FilePicker(self.project_root), _done)

    def action_external_editor(self) -> None:
        from hex_cli.editor_ext import compose_in_external_editor, resolve_editor
        if not resolve_editor():
            self._post_status("Set EDITOR, VISUAL, or HEX_EDITOR to use external compose.")
            return
        try:
            ta = self.query_one("#prompt-input")
            initial = getattr(ta, "text", "") or ""
        except Exception:
            initial = ""
        # External editor blocks — run and reload
        result = compose_in_external_editor(initial)
        if result is None:
            self._post_status("External editor cancelled or unavailable.")
            return
        try:
            ta = self.query_one("#prompt-input")
            if hasattr(ta, "load_text"):
                ta.load_text(result)
            elif hasattr(ta, "clear") and hasattr(ta, "insert"):
                ta.clear()
                ta.insert(result)
            self.query_one(InputPanel).focus_input()
            self._post_status("Loaded text from external editor.")
        except Exception as e:
            self._post_error(str(e))

    def action_redo_change(self) -> None:
        if not self._agent:
            self._post_status("Agent not ready.")
            return
        result = self._agent.changes.redo_last()
        if result.get("ok"):
            self._post_system(f"Redo: {result.get('path')} ({result.get('action')})")
        else:
            self._post_error(result.get("error", "redo failed"))

    def action_set_theme(self, theme_id: str = "hex-dark") -> None:
        from hex_cli.tui.themes import get_theme
        from hex_cli.tui.theme import HEX_CSS
        theme = get_theme(theme_id)
        css = HEX_CSS + ("\n" + theme.css if theme.css else "")
        try:
            self.stylesheet.add_source(css, path=f"hex-theme-{theme.id}")
            self.refresh_css()
            self._post_system(f"Theme: {theme.name}")
        except Exception:
            # fallback: store preference only
            self.state.status_message = f"Theme preferred: {theme.name}"
            self._post_system(f"Theme preference: {theme.name} (restart may be required)")


    def _show_themes(self) -> None:
        from hex_cli.tui.themes import list_themes
        lines = [f"• {t.id} — {t.name}" for t in list_themes()]
        self._post_system("Themes:\n" + "\n".join(lines) + "\n\nApply: /theme <id>")

    def action_command_palette(self) -> None:
        def _done(action_id: str | None) -> None:
            if action_id:
                self._run_palette_action(action_id)
        self.push_screen(CommandPalette(), _done)

    def _run_palette_action(self, action_id: str) -> None:
        if action_id == "new_session":
            self.action_new_session()
        elif action_id == "sessions":
            rows = self.state.session_names()
            lines = [f"{'*' if a else ' '} {n} ({i})" for i, n, a in rows]
            self._post_system("Sessions:\n" + ("\n".join(lines) if lines else "No sessions."))
        elif action_id == "models":
            self.action_pick_model()
        elif action_id == "agents":
            from hex_cli.agents import list_agents
            cur = getattr(self.state, "agent", "general")
            lines = [f"{'*' if a.id == cur else ' '} {a.display_name} ({a.id}) — {a.description}" for a in list_agents()]
            self._post_system("Agents:\n" + "\n".join(lines) + "\n\nSwitch: /agent <name>")
        elif action_id == "connect":
            self.action_connect_provider()
        elif action_id == "providers":
            self.action_show_providers()
        elif action_id == "settings":
            self.action_show_settings()
        elif action_id == "export":
            self._export_conversation()
        elif action_id == "compact":
            self._compact_session()
        elif action_id == "clear":
            self.action_clear_chat()
        elif action_id == "toggle_sidebar":
            self.action_toggle_sidebar()
        elif action_id == "help":
            self.action_show_help()
        elif action_id == "quit":
            self.action_quit_app()
        elif action_id in ("init", "diff", "undo", "tools", "permissions", "save", "history", "mcp", "skills"):
            class _Evt:
                def __init__(self, t: str) -> None:
                    self.text = t
            self.handle_prompt(_Evt("/" + action_id))
        else:
            self._post_status(f"Unknown action: {action_id}")

    

    def action_open_diff_review(self) -> None:
        """Mount interactive DiffReviewPanel for pending ChangeTracker entries."""
        if not self._agent or not self._agent.changes.records:
            self._post_status("No agent changes recorded in this session.")
            return
        s = self._agent.changes.summary()
        files = ", ".join(f["path"] for f in s.get("files", [])[:12])
        self._post_system(
            f"Changes ready for review — {s['file_count']} files  "
            f"+{s['added']}/-{s['removed']}\n{files}\n"
            "Opening Diff Review (A accept · R reject · ← → navigate)."
        )
        # Remove existing panel if any
        try:
            old = self.query_one("#diff-review", DiffReviewPanel)
            old.remove()
        except Exception:
            pass
        try:
            chat = self.query_one(ChatLog)
            panel = DiffReviewPanel(self._agent.changes)
            chat.mount(panel)
            chat.scroll_end(animate=False)
            panel.focus()
        except Exception as e:
            self._post_error(f"Diff review failed: {e}")

    def on_diff_accept(self, event: DiffAccept) -> None:
        if not self._agent:
            return
        result = self._agent.changes.accept_file(event.path)
        try:
            panel = self.query_one("#diff-review", DiffReviewPanel)
            if result.get("ok"):
                panel.remove_path(event.path, f"Accepted {event.path}")
                self._post_system(f"Accepted changes for {event.path}")
            else:
                panel.status_note = result.get("error", "accept failed")
                panel._refresh()
                self._post_error(result.get("error", "accept failed"))
            if not panel.paths:
                panel.remove()
        except Exception:
            pass

    def on_diff_reject(self, event: DiffReject) -> None:
        if not self._agent:
            return
        result = self._agent.changes.reject_file(event.path)
        try:
            panel = self.query_one("#diff-review", DiffReviewPanel)
            if result.get("ok"):
                panel.remove_path(event.path, f"Rejected {event.path} ({result.get('action')})")
                self._post_system(
                    f"Rejected {event.path}: {result.get('action', 'restored')}"
                )
            else:
                panel.status_note = result.get("error", "reject failed")
                panel._refresh()
                self._post_error(result.get("error", "reject failed"))
            if not panel.paths:
                panel.remove()
        except Exception:
            pass

    def on_diff_review_closed(self, event: DiffReviewClosed) -> None:
        try:
            self.query_one("#diff-review", DiffReviewPanel).remove()
        except Exception:
            pass

    def action_copy_code(self) -> None:
        """Copy the last fenced code block from the stream or last assistant message."""
        from hex_cli.tui.markdown_util import last_code_block, extract_code_blocks
        code = None
        buf = getattr(self, "_stream_buf", "") or ""
        if buf:
            block = last_code_block(buf)
            if block:
                code = block[1]
        if code is None:
            # scan state messages
            try:
                for entry in reversed(list(self.state.messages)):
                    if entry.kind == "assistant":
                        blocks = extract_code_blocks(entry.text)
                        if blocks:
                            code = blocks[-1][1]
                            break
            except Exception:
                pass
        if not code:
            self._post_status("No code block to copy.")
            return
        try:
            self.copy_to_clipboard(code)
            self._post_status(f"Copied {len(code)} chars to clipboard.")
        except Exception as e:
            self._post_status(f"Clipboard failed: {e}")

    def action_stop_agent(self) -> None:
        if self._agent and self.state.busy:
            self._agent.request_cancel()
            self._post_status("Cancellation requested…")
        else:
            self._post_status("Nothing running to stop.")

    def _export_conversation(self) -> None:
        import time
        lines = [
            "# HEX session export",
            "",
            f"Project: `{self.project_root}`",
            f"Model: {self.state.model}",
            f"Agent: {getattr(self.state, 'agent', 'general')}",
            "",
            "---",
            "",
        ]
        for e in self.state.entries:
            lines.append(f"### {e.kind.upper()}")
            lines.append("")
            lines.append(e.text)
            lines.append("")
        out = self.project_root / f".hex-export-{int(time.time())}.md"
        try:
            out.write_text("\n".join(lines), encoding="utf-8")
            self._post_system(f"Exported conversation → {out.name}")
        except OSError as exc:
            self._post_error(f"Export failed: {exc}")

    def _compact_session(self) -> None:
        entries = list(self.state.entries)
        if len(entries) <= 4:
            self._post_status("Session already short; nothing to compact.")
            return
        keep = entries[-4:]
        summary_bits = []
        for e in entries[:-4]:
            if e.kind in ("user", "assistant") and e.text:
                summary_bits.append(f"- [{e.kind}] {e.text[:120].replace(chr(10), ' ')}")
        self.state.clear_conversation()
        self.query_one(ChatLog).clear_messages(banner="[dim]Session compacted.[/]")
        if summary_bits:
            self._post_system("Prior context summary:\n" + "\n".join(summary_bits[:20]))
        for e in keep:
            self.state.add(e.kind, e.text, **(e.meta or {}))
            self.query_one(ChatLog).append_entry(e)
        self._post_status("Compacted older messages into a short summary.")


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
