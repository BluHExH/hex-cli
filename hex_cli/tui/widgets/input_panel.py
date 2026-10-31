"""HEX multiline prompt composer.

Enter        → send
Shift+Enter  → newline (also Ctrl+J)
Tab          → accept slash suggestion
Esc          → hide suggestions
"""

from __future__ import annotations

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Static, TextArea

SLASH_COMMANDS: list[tuple[str, str]] = [
    ("/help", "Show help and shortcuts"),
    ("/connect", "Connect a provider / enter API key"),
    ("/models", "Browse and select models"),
    ("/providers", "List connected providers"),
    ("/agent", "Show or switch specialized agents"),
    ("/agents", "List agents (build, plan, explore, general)"),
    ("/plan", "Switch to Plan agent / plan a task"),
    ("/build", "Switch to Build agent / implement a task"),
    ("/explore", "Switch to Explore agent / investigate code"),
    ("/diff", "Show agent code changes"),
    ("/undo", "Restore the last agent file change"),
    ("/redo", "Re-apply last undone change"),
    ("/tools", "List available agent tools"),
    ("/permissions", "Show permission modes"),
    ("/init", "Analyze project and summarize structure"),
    ("/new", "Start a new session"),
    ("/clear", "Clear current conversation"),
    ("/sessions", "List in-memory sessions"),
    ("/save", "Persist current session to disk"),
    ("/history", "List saved sessions for this project"),
    ("/mcp", "MCP servers and tools"),
    ("/skills", "List available skills"),
    ("/worktree", "Git worktree management"),
    ("/lsp", "Language server status"),
    ("/files", "Fuzzy file picker"),
    ("/editor", "Compose in external editor"),
    ("/theme", "Switch UI theme"),
    ("/export", "Export conversation to Markdown"),
    ("/compact", "Compact session context"),
    ("/status", "Show connection status"),
    ("/exit", "Quit HEX"),
]


class PromptSubmitted(Message):
    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text


class InputPanel(Static):
    """Large multiline composer always visible at the bottom."""

    def __init__(self, **kwargs) -> None:
        super().__init__(id="composer", **kwargs)
        self._suggest_index = 0
        self._filtered: list[tuple[str, str]] = []
        self._busy = False

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="composer-meta"):
                yield Static("agent: general", id="composer-agent")
                yield Static("model: —", id="composer-model")
                yield Static(
                    "Enter send · Shift+Enter newline · / commands · Ctrl+. stop",
                    id="composer-hint",
                )
            yield Static("", id="cmd-suggest")
            yield TextArea("", id="prompt-input", show_line_numbers=False)
            yield Static(
                "  Type a coding task…  ·  Ctrl+N new  ·  Ctrl+B sidebar  ·  Ctrl+P palette  ·  Ctrl+F files",
                id="composer-footer",
            )

    def on_mount(self) -> None:
        try:
            ta = self.query_one("#prompt-input", TextArea)
            ta.show_line_numbers = False
        except Exception:
            pass

    def focus_input(self) -> None:
        try:
            self.query_one("#prompt-input", TextArea).focus()
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
            if busy:
                hint.update("Agent running…  Ctrl+. to stop  ·  Enter queues after finish")
            else:
                hint.update("Enter send · Shift+Enter newline · / commands · Ctrl+. stop")
        except Exception:
            pass

    def clear_input(self) -> None:
        try:
            self.query_one("#prompt-input", TextArea).clear()
        except Exception:
            pass

    def get_text(self) -> str:
        try:
            return self.query_one("#prompt-input", TextArea).text
        except Exception:
            return ""

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
        ta = self.query_one("#prompt-input", TextArea)
        ta.clear()
        ta.insert(cmd + " ")
        self._show_suggestions("")
        ta.focus()

    @on(TextArea.Changed, "#prompt-input")
    def on_text_changed(self, event: TextArea.Changed) -> None:
        text = event.text_area.text
        first = text.splitlines()[0] if text else ""
        if first.startswith("/") and "\n" not in text.strip():
            self._show_suggestions(first.strip())
        else:
            self._show_suggestions("")

    def on_key(self, event: events.Key) -> None:
        try:
            ta = self.query_one("#prompt-input", TextArea)
        except Exception:
            return
        if not ta.has_focus:
            return

        # Shift+Enter / Ctrl+J → allow default newline in TextArea
        if event.key in ("shift+enter", "ctrl+j"):
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

        if event.key == "enter":
            text = ta.text.strip()
            if not text:
                event.prevent_default()
                event.stop()
                return
            event.prevent_default()
            event.stop()
            ta.clear()
            self._show_suggestions("")
            self.post_message(PromptSubmitted(text))
            return

        if event.key == "escape" and self._filtered:
            event.prevent_default()
            event.stop()
            self._show_suggestions("")
