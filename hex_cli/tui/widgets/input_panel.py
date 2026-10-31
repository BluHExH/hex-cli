"""Bottom multiline input with slash-command suggestions."""

from __future__ import annotations

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Static, TextArea

SLASH_COMMANDS: list[tuple[str, str]] = [
    ("/help", "Show help and shortcuts"),
    ("/connect", "Connect a provider / enter API key"),
    ("/models", "Browse and select models"),
    ("/providers", "List connected providers"),
    ("/disconnect", "Remove stored API key"),
    ("/settings", "Show settings"),
    ("/agent", "Show or switch specialized agents"),
    ("/agents", "List agents (build, plan, explore, general)"),
    ("/plan", "Switch to Plan agent / plan a task"),
    ("/build", "Switch to Build agent / implement a task"),
    ("/explore", "Switch to Explore agent / investigate code"),
    ("/diff", "Show agent code changes"),
    ("/undo", "Restore the last agent file change"),
    ("/tools", "List available agent tools"),
    ("/permissions", "Show permission modes"),
    ("/init", "Analyze project and summarize structure"),
    ("/new", "Start a new session"),
    ("/clear", "Clear current conversation"),
    ("/sessions", "List in-memory sessions"),
    ("/save", "Persist current session to disk"),
    ("/history", "List saved sessions for this project"),
    ("/session rename", "Rename the active session"),
    ("/session delete", "Delete the active session"),
    ("/session search", "Search saved sessions"),
    ("/status", "Show connection status"),
    ("/exit", "Quit HEX"),
]


class PromptSubmitted(Message):
    """User submitted a prompt."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text


class InputPanel(Static):
    """Multiline prompt with command palette hints."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._suggest_index = 0
        self._filtered: list[tuple[str, str]] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="input-wrap"):
            yield Static("", id="cmd-suggest")
            yield Static(
                "Enter send · Ctrl+J newline · / commands · Ctrl+P models · Ctrl+N new",
                id="input-bar",
            )
            yield TextArea(id="prompt-input")

    def focus_input(self) -> None:
        try:
            self.query_one("#prompt-input", TextArea).focus()
        except Exception:
            pass

    def get_text(self) -> str:
        try:
            return self.query_one("#prompt-input", TextArea).text
        except Exception:
            return ""

    def clear_input(self) -> None:
        try:
            ta = self.query_one("#prompt-input", TextArea)
            ta.load_text("")
        except Exception:
            pass
        self._hide_suggestions()

    def _filter_commands(self, prefix: str) -> list[tuple[str, str]]:
        p = prefix.lower().strip()
        if not p.startswith("/"):
            return []
        return [(c, d) for c, d in SLASH_COMMANDS if c.startswith(p)]

    def _show_suggestions(self, items: list[tuple[str, str]]) -> None:
        self._filtered = items
        self._suggest_index = min(self._suggest_index, max(0, len(items) - 1))
        try:
            box = self.query_one("#cmd-suggest", Static)
            if not items:
                box.update("")
                box.remove_class("visible")
                return
            lines = []
            for i, (cmd, desc) in enumerate(items[:8]):
                mark = "▸ " if i == self._suggest_index else "  "
                style = "bold #c084fc" if i == self._suggest_index else "dim"
                lines.append(f"[{style}]{mark}{cmd}[/{style}]  [dim]{desc}[/]")
            box.update("\n".join(lines))
            box.add_class("visible")
        except Exception:
            pass

    def _hide_suggestions(self) -> None:
        self._filtered = []
        try:
            box = self.query_one("#cmd-suggest", Static)
            box.update("")
            box.remove_class("visible")
        except Exception:
            pass

    def _refresh_suggest_highlight(self) -> None:
        if self._filtered:
            self._show_suggestions(self._filtered)

    @on(TextArea.Changed, "#prompt-input")
    def on_text_changed(self, event: TextArea.Changed) -> None:
        text = event.text_area.text
        first_line = text.split("\n", 1)[0]
        if first_line.startswith("/") and "\n" not in text.strip():
            self._suggest_index = 0
            self._show_suggestions(self._filter_commands(first_line))
        else:
            self._hide_suggestions()

    def on_key(self, event: events.Key) -> None:
        if self._filtered and event.key in ("down", "up", "tab"):
            n = len(self._filtered)
            if event.key == "down":
                self._suggest_index = (self._suggest_index + 1) % n
            elif event.key == "up":
                self._suggest_index = (self._suggest_index - 1) % n
            elif event.key == "tab":
                cmd = self._filtered[self._suggest_index][0]
                try:
                    ta = self.query_one("#prompt-input", TextArea)
                    ta.load_text(cmd + " ")
                    ta.focus()
                except Exception:
                    pass
                self._hide_suggestions()
                event.prevent_default()
                event.stop()
                return
            self._refresh_suggest_highlight()
            event.prevent_default()
            event.stop()
            return

        if event.key == "enter":
            if event.shift:
                return
            if self._filtered:
                cmd = self._filtered[self._suggest_index][0]
                self._hide_suggestions()
                self.clear_input()
                self.post_message(PromptSubmitted(cmd))
                event.prevent_default()
                event.stop()
                return
            text = self.get_text().strip()
            if text:
                self.clear_input()
                self.post_message(PromptSubmitted(text))
            event.prevent_default()
            event.stop()
