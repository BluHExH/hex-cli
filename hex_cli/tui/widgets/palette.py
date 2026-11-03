from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label, OptionList
from textual.widgets.option_list import Option


COMMANDS = [
    ("new_session", "New session", "ctrl+n"),
    ("toggle_sidebar", "Toggle sidebar", "ctrl+b"),
    ("focus_composer", "Focus composer", "ctrl+l"),
    ("cancel", "Cancel current turn", "ctrl+c"),
    ("help", "Show help", "?"),
    ("quit", "Quit HEX", "ctrl+q"),
]


class CommandPalette(ModalScreen[str | None]):
    """Simple command palette."""

    CSS = """
    CommandPalette { align: center middle; }
    #palette-box {
        width: 60;
        height: auto;
        max-height: 20;
        background: #111820;
        border: solid #7c6aef;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="palette-box"):
            yield Label("[bold]Commands[/]")
            yield OptionList(
                *[Option(f"{label}   [dim]{keys}[/]", id=cmd) for cmd, label, keys in COMMANDS],
                id="palette-list",
            )

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(str(event.option.id) if event.option.id else None)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
