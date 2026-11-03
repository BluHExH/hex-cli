from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, OptionList
from textual.widgets.option_list import Option

COMMANDS = [
    ("new_session", "New Session", "Ctrl+N"),
    ("toggle_left", "Toggle Left Sidebar", "Ctrl+B"),
    ("toggle_right", "Toggle Right Sidebar", "Ctrl+L"),
    ("focus_composer", "Focus Composer", ""),
    ("cancel", "Cancel Turn", "Esc"),
    ("quit", "Quit", "Ctrl+Q"),
]


class CommandPalette(ModalScreen[str | None]):
    CSS = """
    CommandPalette { align: center middle; }
    #palette-box {
        width: 64; height: auto; max-height: 18;
        background: #141a22; border: solid #8b7cf7; padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="palette-box"):
            yield Label("[bold]Command Palette[/]")
            yield OptionList(
                *[Option(f"{label}  [dim]{keys}[/]", id=cmd) for cmd, label, keys in COMMANDS],
                id="plist",
            )

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(str(event.option.id) if event.option.id else None)

    def on_key(self, event) -> None:  # noqa: ANN001
        if event.key == "escape":
            self.dismiss(None)
