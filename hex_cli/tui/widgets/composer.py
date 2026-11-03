from __future__ import annotations

from textual.message import Message
from textual.widgets import TextArea


class PromptComposer(TextArea):
    """Multi-line prompt composer with Enter-to-send (plain), Shift+Enter newline via soft wrap."""

    class Submitted(Message):
        def __init__(self, text: str) -> None:
            super().__init__()
            self.text = text

    BINDINGS = [
        ("ctrl+enter", "submit", "Send"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(id="composer", soft_wrap=True, show_line_numbers=False, **kwargs)
        self._history: list[str] = []
        self._hist_idx = -1
        self._busy = False

    def on_mount(self) -> None:
        self.border_title = "Message"
        self.border_subtitle = "Ctrl+Enter send"

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.disabled = busy
        self.border_subtitle = "working…" if busy else "Ctrl+Enter send"

    def action_submit(self) -> None:
        if self._busy:
            return
        text = self.text.strip()
        if not text:
            return
        self._history.append(text)
        self._hist_idx = len(self._history)
        self.clear()
        self.post_message(self.Submitted(text))

    def action_history_up(self) -> None:
        if not self._history:
            return
        self._hist_idx = max(0, self._hist_idx - 1)
        self.load_text(self._history[self._hist_idx])

    def action_history_down(self) -> None:
        if not self._history:
            return
        self._hist_idx = min(len(self._history), self._hist_idx + 1)
        if self._hist_idx >= len(self._history):
            self.clear()
        else:
            self.load_text(self._history[self._hist_idx])
