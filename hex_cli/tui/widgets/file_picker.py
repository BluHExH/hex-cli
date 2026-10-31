"""Fuzzy project file picker for @-references."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, OptionList, Static
from textual.widgets.option_list import Option

from hex_cli.tui.file_index import list_project_files, fuzzy_score


class FilePicker(ModalScreen[str | None]):
    """Keyboard-navigable fuzzy file picker. Returns relative path or None."""

    CSS = """
    FilePicker { align: center middle; }
    #fp-box {
        width: 76; max-width: 96%; height: auto; max-height: 85%;
        background: #161b22; border: tall #58a6ff; padding: 1 1;
    }
    #fp-title { color: #58a6ff; text-style: bold; margin-bottom: 1; }
    #fp-filter { margin-bottom: 1; background: #0d1117; border: tall #30363d; }
    #fp-list { height: 18; min-height: 10; border: tall #21262d; background: #0d1117; }
    #fp-preview {
        height: 6; max-height: 8; border: tall #21262d; background: #0d1117;
        color: #8b949e; margin-top: 1;
    }
    """

    def __init__(self, project_root: Path) -> None:
        super().__init__()
        self.project_root = project_root.resolve()
        self._files = list_project_files(self.project_root)
        self._filtered: list[str] = list(self._files)

    def compose(self) -> ComposeResult:
        with Vertical(id="fp-box"):
            yield Static("File picker — type to filter, Enter to insert @path", id="fp-title")
            yield Input(placeholder="Search files…", id="fp-filter")
            yield OptionList(id="fp-list")
            yield Static("", id="fp-preview")

    def on_mount(self) -> None:
        self._populate("")
        self.query_one("#fp-filter", Input).focus()

    def _populate(self, query: str) -> None:
        scored: list[tuple[int, str]] = []
        for path in self._files:
            sc = fuzzy_score(query, path)
            if sc >= 0:
                scored.append((sc, path))
        scored.sort(key=lambda x: (-x[0], x[1]))
        self._filtered = [p for _, p in scored[:80]]
        ol = self.query_one("#fp-list", OptionList)
        ol.clear_options()
        for path in self._filtered:
            ol.add_option(Option(path, id=path.replace("/", "__")))
        self._update_preview(self._filtered[0] if self._filtered else None)

    def _update_preview(self, rel: str | None) -> None:
        box = self.query_one("#fp-preview", Static)
        if not rel:
            box.update("[dim]No match[/]")
            return
        path = self.project_root / rel
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            preview = "\n".join(text.splitlines()[:6])
            if len(preview) > 400:
                preview = preview[:400] + "…"
            box.update(f"[dim]{rel}[/]\n{preview.replace('[', '\\[')}")
        except OSError as e:
            box.update(f"[dim]{rel}[/]\n{e}")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "fp-filter":
            self._populate(event.value)

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        opt = event.option
        if opt and opt.id:
            self._update_preview(str(opt.id).replace("__", "/"))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        opt = event.option
        if opt and opt.id:
            self.dismiss(str(opt.id).replace("__", "/"))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(self._filtered[0] if self._filtered else None)

    def on_key(self, event) -> None:  # noqa: ANN001
        if event.key == "escape":
            self.dismiss(None)
