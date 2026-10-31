"""Bottom multiline input panel."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Static, TextArea


class PromptSubmitted(Message):
    """User submitted a prompt."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text


class InputPanel(Static):
    """Multiline prompt with shortcut hints."""

    def compose(self) -> ComposeResult:
        with Vertical(id="input-panel"):
            yield Static(
                "Enter submit \u00b7 Ctrl+J newline \u00b7 Ctrl+P model \u00b7 Ctrl+B sidebar \u00b7 Ctrl+H help",
                id="input-hints",
            )
            yield TextArea(id="prompt-input", classes="")

    def on_mount(self) -> None:
        ta = self.query_one("#prompt-input", TextArea)
        ta.show_line_numbers = False
        ta.tab_behavior = "indent"

    def focus_input(self) -> None:
        try:
            self.query_one("#prompt-input", TextArea).focus()
        except Exception:
            pass

    def clear_input(self) -> None:
        try:
            self.query_one("#prompt-input", TextArea).clear()
        except Exception:
            pass

    def on_text_area_submitted(self, event: TextArea.Submitted) -> None:
        text = event.text_area.text.strip()
        if text:
            self.post_message(PromptSubmitted(text))
            event.text_area.clear()
