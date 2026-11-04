from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Input, Static

from hex_cli.tui.commands import match as match_commands


class PromptComposer(Vertical):
    """OpenCode-style composer: blue-left block, mode · model · provider row."""

    class Submitted(Message):
        def __init__(self, text: str) -> None:
            super().__init__()
            self.text = text

    class ModeChanged(Message):
        def __init__(self) -> None:
            super().__init__()

    def __init__(self) -> None:
        super().__init__(id="composer-dock")
        self._busy = False
        self._mode = "build"
        self._provider = "mock"
        self._model = "mock-smart"

    def compose(self) -> ComposeResult:
        yield Static("", id="command-hints")
        yield Input(id="composer-box")
        yield Static("", id="composer-meta")

    def on_mount(self) -> None:
        self.query_one("#composer-box", Input).focus()

    # -- meta row --------------------------------------------------------
    def _render_meta(self) -> None:
        mode = "[bold #4d9eff]" + ("Build" if self._mode == "build" else "Plan") + "[/]"
        suffix = "  [dim](read-only)[/]" if self._mode != "build" and self._busy is False else ""
        busy = "[yellow]…[/]" if self._busy else ""
        model = f"[bold]{self._model}[/]  [dim]HEX[/]"
        self.query_one("#composer-meta", Static).update(f"{mode}  {model}{suffix}{busy}")

    def set_mode(self, mode: str) -> None:
        self._mode = mode
        self._render_meta()

    def set_model(self, provider: str, model: str) -> None:
        self._provider, self._model = provider, model
        self._render_meta()

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.query_one("#composer-box", Input).disabled = busy
        self._render_meta()

    def set_permission_label(self, mode: str) -> None:  # kept for compatibility
        self.set_mode("build" if mode != "deny" else self._mode)

    # -- hints -----------------------------------------------------------
    def _update_hints(self, value: str) -> None:
        hints = self.query_one("#command-hints", Static)
        head = value.split(" ")[0] if value.startswith("/") else ""
        matches = match_commands(head) if head else []
        if not matches or self._busy:
            hints.update("")
            hints.display = False
            return
        rows = "\n".join(f"[bold #4d9eff]/{name}[/]  [dim]{desc}[/]" for name, desc in matches[:6])
        hints.update(rows)
        hints.display = True

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "composer-box":
            self._update_hints(event.value)

    # -- submit ----------------------------------------------------------
    def _complete_hint(self, head: str) -> bool:
        matches = match_commands(head)
        if len(matches) >= 1:
            self.query_one("#composer-box", Input).value = f"/{matches[0][0]} "
            return True
        return False

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "composer-box":
            return
        text = event.value.strip()
        head = text.split(" ")[0]
        if text.startswith("/") and match_commands(head) and not any(
            c.lower() == head.lstrip("/") for c, _ in match_commands(head)
        ):
            # partial command (e.g. "/ses") — complete first, don't submit
            if self._complete_hint(head):
                return
        event.input.value = ""
        self._update_hints("")
        if text and not self._busy:
            self.post_message(self.Submitted(text))

    def focus_input(self) -> None:
        self.query_one("#composer-box", Input).focus()
