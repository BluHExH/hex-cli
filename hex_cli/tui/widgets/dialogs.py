"""OpenCode-style modal dialogs: command search, sessions, models."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label, OptionList
from textual.widgets.option_list import Option

from hex_cli.tui.commands import CANONICAL

DIALOG_CSS = """
#dialog-box {
    width: 74; max-height: 24;
    background: #10131a;
    border: solid #262b36;
    padding: 1 2;
}
#dialog-title { color: #7d8590; }
#dialog-search { border: none; height: 1; padding: 0 1; margin-bottom: 1; color: #e8eaef; }
#dialog-list { background: transparent; height: auto; max-height: 16; color: #e8eaef; }
"""


class DialogBase(ModalScreen):
    """Centered dialog: optional search + option list, Esc closes with None."""

    TITLE_LABEL = ""
    WITH_SEARCH = False

    CSS = DIALOG_CSS

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog-box"):
            if self.TITLE_LABEL:
                yield Label(self.TITLE_LABEL, id="dialog-title")
            if self.WITH_SEARCH:
                yield Input(placeholder="Search commands…", id="dialog-search")
            yield self._list_widget()

    def _list_widget(self) -> OptionList:
        raise NotImplementedError

    def on_key(self, event) -> None:  # noqa: ANN001
        if event.key == "escape":
            self.dismiss(None)


class CommandDialog(DialogBase):
    """Searchable slash-command dialog (ctrl+p / /help)."""

    TITLE_LABEL = "Commands"
    WITH_SEARCH = True

    def __init__(self, extra_rows: list[tuple[str, str]] | None = None) -> None:
        super().__init__()
        self._all = [(f"/{n}", d) for n, d in CANONICAL] + list(extra_rows or [])

    def _list_widget(self) -> OptionList:
        return self._build()

    def _build(self, query: str = "") -> OptionList:
        q = query.strip().lower().lstrip("/")
        rows = [(n, d) for n, d in self._all if q in n.lower() or q in d.lower()]
        opts = [Option(f"{n}  [dim]{d}[/]", id=n) for n, d in rows]
        return OptionList(*opts, id="dialog-list")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "dialog-search":
            return
        old = self.query_one("#dialog-list", OptionList)
        old.remove()
        self.query_one("#dialog-box", Vertical).mount(self._build(event.value))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(str(event.option.id) if event.option.id else None)


class SessionsDialog(DialogBase):
    """Session picker fed by SessionStore sessions."""

    TITLE_LABEL = "Sessions"

    def __init__(self, rows: list[tuple[str, str, str]]) -> None:
        super().__init__()
        self._rows = rows

    def _list_widget(self) -> OptionList:
        opts = [Option(f"[bold]{t}[/]  [dim]{u}[/]", id=i) for t, u, i in self._rows]
        return OptionList(*opts, id="dialog-list")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(str(event.option.id) if event.option.id else None)


class ModelsDialog(DialogBase):
    """Model/provider picker (only configured providers are selectable)."""

    TITLE_LABEL = "Models"

    def __init__(self, rows: list[tuple[str, bool]]) -> None:
        super().__init__()
        self._rows = rows

    def _list_widget(self) -> OptionList:
        items = []
        for label, active in self._rows:
            mark = "[green]●[/]" if active else "[dim]○[/]"
            items.append(Option(f"{mark} {label}", id=label if active else None))
        return OptionList(*items, id="dialog-list")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(str(event.option.id) if event.option.id else None)
