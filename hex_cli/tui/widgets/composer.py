from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Input, Static


class PromptComposer(Vertical):
    """Reference composer: Ask anything… + bottom chips + Enter affordance."""

    class Submitted(Message):
        def __init__(self, text: str) -> None:
            super().__init__()
            self.text = text

    def __init__(self) -> None:
        super().__init__(id="composer-dock")
        self._busy = False

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Ask anything…", id="composer-box")
        yield Static(
            "[dim]+ Add Context[/]    [dim]{ } Tools ▾[/]    [green]●[/] [dim]Auto[/]"
            "                              [bold]↵ Enter ▸[/]",
            id="composer-toolbar",
        )

    def on_mount(self) -> None:
        self.query_one("#composer-box", Input).focus()

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        box = self.query_one("#composer-box", Input)
        box.disabled = busy
        box.placeholder = "Working…" if busy else "Ask anything…"

    def set_permission_label(self, mode: str) -> None:
        chip = {
            "allow": "[green]●[/] [dim]Auto[/]",
            "deny": "[red]●[/] [dim]Deny[/]",
            "prompt": "[yellow]●[/] [dim]Prompt[/]",
        }.get(mode, mode)
        self.query_one("#composer-toolbar", Static).update(
            f"[dim]+ Add Context[/]    [dim]{{ }} Tools ▾[/]    {chip}"
            "                              [bold]↵ Enter ▸[/]"
        )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "composer-box" or self._busy:
            return
        text = event.value.strip()
        event.input.value = ""
        if text:
            self.post_message(self.Submitted(text))

    def focus_input(self) -> None:
        self.query_one("#composer-box", Input).focus()
