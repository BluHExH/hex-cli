"""HEX multiline prompt composer with reliable Enter-to-send.

Root cause of Enter-not-sending: TextArea consumes Enter for newlines before
parent on_key handlers. Fix: subclass TextArea with priority BINDINGS so
Enter submits and Shift+Enter / Ctrl+J inserts a newline.
"""

from __future__ import annotations

from textual import events, on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Static, TextArea

SLASH_COMMANDS: list[tuple[str, str]] = [
    ("/help", "Show help and shortcuts"),
    ("/connect", "Connect a provider / enter API key"),
    ("/models", "Browse and select models"),
    ("/providers", "List connected providers"),
    ("/agent", "Show or switch specialized agents"),
    ("/agents", "List agents"),
    ("/plan", "Plan agent / plan a task"),
    ("/build", "Build agent / implement a task"),
    ("/explore", "Explore agent / investigate code"),
    ("/diff", "Show agent code changes"),
    ("/undo", "Undo last agent file change"),
    ("/redo", "Redo last undone change"),
    ("/tools", "List agent tools"),
    ("/permissions", "Permission modes"),
    ("/init", "Analyze project"),
    ("/new", "New session"),
    ("/clear", "Clear conversation"),
    ("/sessions", "List sessions"),
    ("/save", "Save session"),
    ("/history", "Saved sessions"),
    ("/mcp", "MCP servers"),
    ("/skills", "Skills"),
    ("/files", "File picker"),
    ("/editor", "External editor"),
    ("/theme", "UI theme"),
    ("/export", "Export chat"),
    ("/compact", "Compact context"),
    ("/status", "Status"),
    ("/exit", "Quit"),
]


class PromptSubmitted(Message):
    """User submitted a non-empty prompt."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text


class PromptTextArea(TextArea):
    """TextArea where Enter submits; Shift+Enter / Ctrl+J inserts newline."""

    BINDINGS = [
        Binding("enter", "submit_prompt", "Send", priority=True, show=False),
        Binding("shift+enter", "insert_newline", "Newline", priority=True, show=False),
        Binding("ctrl+j", "insert_newline", "Newline", priority=True, show=False),
    ]

    def action_submit_prompt(self) -> None:
        # If parent is in @ file-pick mode, accept file instead of sending
        try:
            parent = self.parent
            while parent is not None and not hasattr(parent, "_at_mode"):
                parent = getattr(parent, "parent", None)
            if parent is not None and getattr(parent, "_at_mode", False) and getattr(parent, "_file_filtered", None):
                parent._accept_file_suggestion()
                return
        except Exception:
            pass
        text = self.text.strip()
        if not text:
            return
        self.clear()
        self.post_message(PromptSubmitted(text))

    def action_insert_newline(self) -> None:
        self.insert("\n")


class InputPanel(Static):
    """Composer: multiline area + send button + slash suggestions."""

    def __init__(self, **kwargs) -> None:
        super().__init__(id="composer", **kwargs)
        self._suggest_index = 0
        self._filtered: list[tuple[str, str]] = []
        self._busy = False
        self._file_filtered: list[str] = []
        self._file_index = 0
        self._at_mode = False
        self._project_root = None


    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="composer-meta"):
                yield Static("agent: general", id="composer-agent")
                yield Static("model: —", id="composer-model")
                yield Static("Enter send · Shift+Enter newline", id="composer-hint")
            yield Static("", id="cmd-suggest")
            with Horizontal(id="composer-row"):
                yield PromptTextArea(id="prompt-input")
                yield Button("Send", id="btn-send", classes="-primary")
                yield Button("Stop", id="btn-stop")
            yield Static(
                "  Ctrl+P palette · Ctrl+F files · Ctrl+N new · Ctrl+B sidebar",
                id="composer-footer",
            )

    def on_mount(self) -> None:
        try:
            ta = self.query_one("#prompt-input", PromptTextArea)
            ta.show_line_numbers = False
        except Exception:
            pass
        try:
            self.query_one("#btn-stop", Button).display = False
        except Exception:
            pass

    def set_project_root(self, root) -> None:
        self._project_root = root

    def focus_input(self) -> None:
        try:
            self.query_one("#prompt-input", PromptTextArea).focus()
        except Exception:
            pass

    def set_meta(self, *, agent: str = "", model: str = "") -> None:
        try:
            if agent:
                self.query_one("#composer-agent", Static).update(f"agent: {agent}")
            if model:
                m = model if len(model) <= 40 else model[:37] + "…"
                self.query_one("#composer-model", Static).update(f"model: {m}")
        except Exception:
            pass

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        try:
            hint = self.query_one("#composer-hint", Static)
            btn = self.query_one("#btn-send", Button)
            stop = self.query_one("#btn-stop", Button)
            if busy:
                hint.update("Working…  Ctrl+. or Stop")
                btn.label = "…"
                btn.disabled = True
                stop.display = True
            else:
                hint.update("Enter send · Shift+Enter newline")
                btn.label = "Send"
                btn.disabled = False
                stop.display = False
        except Exception:
            pass

    def clear_input(self) -> None:
        try:
            self.query_one("#prompt-input", PromptTextArea).clear()
        except Exception:
            pass

    def get_text(self) -> str:
        try:
            return self.query_one("#prompt-input", PromptTextArea).text
        except Exception:
            return ""

    def _submit_current(self) -> None:
        ta = self.query_one("#prompt-input", PromptTextArea)
        text = ta.text.strip()
        if not text:
            return
        ta.clear()
        self._show_suggestions("")
        self.post_message(PromptSubmitted(text))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-send":
            event.stop()
            self._submit_current()
        elif event.button.id == "btn-stop":
            event.stop()
            try:
                self.app.action_stop_agent()
            except Exception:
                pass

    def _show_suggestions(self, prefix: str) -> None:
        box = self.query_one("#cmd-suggest", Static)
        if not prefix.startswith("/"):
            box.remove_class("visible")
            box.update("")
            self._filtered = []
            return
        q = prefix.lower().strip()
        self._filtered = [
            (c, d) for c, d in SLASH_COMMANDS if c.startswith(q) or q[1:] in c
        ]
        self._suggest_index = 0
        if not self._filtered:
            box.remove_class("visible")
            box.update("")
            return
        lines = []
        for i, (cmd, desc) in enumerate(self._filtered[:8]):
            mark = "▸" if i == self._suggest_index else " "
            lines.append(f"{mark} {cmd}  [dim]{desc}[/]")
        box.update("\n".join(lines))
        box.add_class("visible")

    def _accept_suggestion(self) -> None:
        if not self._filtered:
            return
        cmd, _ = self._filtered[self._suggest_index]
        ta = self.query_one("#prompt-input", PromptTextArea)
        ta.clear()
        ta.insert(cmd + " ")
        self._show_suggestions("")
        ta.focus()

    @on(TextArea.Changed, "#prompt-input")
    def on_text_changed(self, event: TextArea.Changed) -> None:
        text = event.text_area.text
        first = text.splitlines()[0] if text else ""
        if first.startswith("/") and "\n" not in text.strip():
            self._at_mode = False
            self._show_suggestions(first.strip())
            return
        # Detect active @ token at end of text
        at = self._active_at_query(text)
        if at is not None:
            self._at_mode = True
            self._show_file_suggestions(at)
        else:
            self._at_mode = False
            self._show_suggestions("")

    def _active_at_query(self, text: str) -> str | None:
        """Return query after last @ if still editing a mention token."""
        if not text or "@" not in text:
            return None
        # only consider last line
        line = text.splitlines()[-1] if text else ""
        idx = line.rfind("@")
        if idx < 0:
            return None
        # char before @ should be start or whitespace/punctuation
        if idx > 0 and line[idx - 1].isalnum():
            return None
        token = line[idx + 1 :]
        if any(c.isspace() for c in token):
            return None
        return token

    def _show_file_suggestions(self, query: str) -> None:
        box = self.query_one("#cmd-suggest", Static)
        if self._project_root is None:
            box.remove_class("visible")
            box.update("")
            self._file_filtered = []
            return
        try:
            from hex_cli.tui.file_index import search_files
            self._file_filtered = search_files(self._project_root, query, limit=12)
        except Exception:
            self._file_filtered = []
        self._file_index = 0
        if not self._file_filtered:
            box.update("[dim]No matching files[/]")
            box.add_class("visible")
            return
        lines = []
        for i, path in enumerate(self._file_filtered[:10]):
            mark = "▸" if i == self._file_index else " "
            lines.append(f"{mark} @{path}")
        box.update("\n".join(lines) + f"\n[dim]{len(self._file_filtered)} matches · Enter/Tab select · Esc close[/]")
        box.add_class("visible")

    def _accept_file_suggestion(self) -> None:
        if not self._file_filtered:
            return
        path = self._file_filtered[self._file_index]
        ta = self.query_one("#prompt-input", PromptTextArea)
        text = ta.text
        # replace active @token with @path
        lines = text.splitlines() or [""]
        last = lines[-1]
        idx = last.rfind("@")
        if idx < 0:
            return
        new_last = last[:idx] + "@" + path + " "
        lines[-1] = new_last
        new_text = "\n".join(lines)
        ta.clear()
        ta.insert(new_text)
        self._at_mode = False
        self._file_filtered = []
        self._show_suggestions("")
        ta.focus()

    def on_key(self, event: events.Key) -> None:
        try:
            ta = self.query_one("#prompt-input", PromptTextArea)
        except Exception:
            return
        if not ta.has_focus:
            return
        if self._at_mode and self._file_filtered:
            if event.key in ("tab", "enter"):
                event.prevent_default()
                event.stop()
                self._accept_file_suggestion()
                return
            if event.key in ("up", "down"):
                event.prevent_default()
                event.stop()
                if event.key == "up":
                    self._file_index = max(0, self._file_index - 1)
                else:
                    self._file_index = min(len(self._file_filtered) - 1, self._file_index + 1)
                self._show_file_suggestions(self._active_at_query(ta.text) or "")
                return
            if event.key == "escape":
                event.prevent_default()
                event.stop()
                self._at_mode = False
                self._file_filtered = []
                self._show_suggestions("")
                return
        if event.key == "tab" and self._filtered:
            event.prevent_default()
            event.stop()
            self._accept_suggestion()
            return
        if event.key in ("up", "down") and self._filtered:
            event.prevent_default()
            event.stop()
            if event.key == "up":
                self._suggest_index = max(0, self._suggest_index - 1)
            else:
                self._suggest_index = min(len(self._filtered) - 1, self._suggest_index + 1)
            lines = []
            for i, (cmd, desc) in enumerate(self._filtered[:8]):
                mark = "▸" if i == self._suggest_index else " "
                lines.append(f"{mark} {cmd}  [dim]{desc}[/]")
            self.query_one("#cmd-suggest", Static).update("\n".join(lines))
            return
        if event.key == "escape" and self._filtered:
            event.prevent_default()
            event.stop()
            self._show_suggestions("")
