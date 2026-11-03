from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.message import Message
from textual.widgets import Input, Static


class PromptComposer(Vertical):
    """Bottom composer with toolbar chips (structure matches reference)."""

    class Submitted(Message):
        def __init__(self, text: str) -> None:
            super().__init__()
            self.text = text

    def __init__(self) -> None:
        super().__init__(id="composer-dock")
        self._busy = False
        self._history: list[str] = []

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Ask anything…", id="composer-box")
        with Horizontal(id="composer-toolbar"):
            yield Static("[dim]+ Context[/]   [dim]{ } Tools[/]   [green]•[/] [dim]permission[/]          [bold]Enter ↵[/]", id="composer-hints")

    def on_mount(self) -> None:
        self.query_one("#composer-box", Input).focus()

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        box = self.query_one("#composer-box", Input)
        box.disabled = busy
        box.placeholder = "Working…" if busy else "Ask anything…"

    def set_permission_label(self, mode: str) -> None:
        hints = self.query_one("#composer-hints", Static)
        label = {
            "allow": "[green]• Auto[/]",
            "deny": "[red]• Deny[/]",
            "prompt": "[yellow]• Prompt[/]",
        }.get(mode, mode)
        hints.update(f"[dim]+ Context[/]   [dim]{{ }} Tools[/]   {label}          [bold]Enter ↵[/]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "composer-box" or self._busy:
            return
        text = event.value.strip()
        event.input.value = ""
        if not text:
            return
        self._history.append(text)
        self.post_message(self.Submitted(text))

    def focus_input(self) -> None:
        self.query_one("#composer-box", Input).focus()
