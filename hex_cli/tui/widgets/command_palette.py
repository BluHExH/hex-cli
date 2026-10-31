"""OpenCode-style command palette (Ctrl+P)."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, OptionList, Static
from textual.widgets.option_list import Option


# (id, label, description)
PALETTE_ACTIONS: list[tuple[str, str, str]] = [
    ("new_session", "New session", "Start a fresh conversation"),
    ("sessions", "Sessions", "List and switch sessions"),
    ("models", "Models", "Browse / select model"),
    ("agents", "Agents", "Switch agent (build / plan / explore / general)"),
    ("connect", "Connect provider", "Add or update API key"),
    ("providers", "Providers", "Show provider connection status"),
    ("settings", "Settings", "Show configuration overview"),
    ("init", "Init project", "Analyze project structure"),
    ("diff", "Diff / review", "Show agent code changes"),
    ("undo", "Undo last change", "Restore last agent file edit"),
    ("tools", "Tools", "List agent tools"),
    ("permissions", "Permissions", "Show permission modes"),
    ("save", "Save session", "Persist session to disk"),
    ("history", "Session history", "List saved sessions"),
    ("mcp", "MCP servers", "List MCP connections"),
    ("skills", "Skills", "List loaded skills"),
    ("export", "Export chat", "Export conversation to Markdown"),
    ("compact", "Compact session", "Summarize and trim context"),
    ("clear", "Clear chat", "Clear current conversation view"),
    ("toggle_sidebar", "Toggle sidebar", "Show or hide the left sidebar"),
    ("help", "Help", "Keyboard shortcuts and commands"),
    ("quit", "Quit", "Exit HEX"),
]


class CommandPalette(ModalScreen[str | None]):
    """Fuzzy-filterable command palette."""

    CSS = """
    CommandPalette {
        align: center middle;
    }
    #palette-box {
        width: 72;
        max-width: 94%;
        height: auto;
        max-height: 80%;
        background: #161b22;
        border: tall #a78bfa;
        padding: 1 1;
    }
    #palette-title {
        color: #a78bfa;
        text-style: bold;
        margin-bottom: 1;
    }
    #palette-filter {
        margin-bottom: 1;
        background: #0d1117;
        border: tall #30363d;
    }
    #palette-list {
        height: 16;
        min-height: 8;
        border: tall #21262d;
        background: #0d1117;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._actions = list(PALETTE_ACTIONS)

    def compose(self) -> ComposeResult:
        with Vertical(id="palette-box"):
            yield Static("Command palette", id="palette-title")
            yield Input(placeholder="Filter commands…", id="palette-filter")
            yield OptionList(id="palette-list")

    def on_mount(self) -> None:
        self._populate("")
        self.query_one("#palette-filter", Input).focus()

    def _populate(self, query: str) -> None:
        q = query.strip().lower()
        ol = self.query_one("#palette-list", OptionList)
        ol.clear_options()
        for aid, label, desc in self._actions:
            hay = f"{label} {desc} {aid}".lower()
            if q and q not in hay:
                continue
            ol.add_option(Option(f"{label}  —  {desc}", id=aid))

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "palette-filter":
            self._populate(event.value)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        opt_id = event.option.id
        if isinstance(opt_id, str):
            self.dismiss(opt_id)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        ol = self.query_one("#palette-list", OptionList)
        if ol.option_count > 0:
            # select first visible
            try:
                first = ol.get_option_at_index(0)
                if first and first.id:
                    self.dismiss(str(first.id))
                    return
            except Exception:
                pass
        self.dismiss(None)

    def on_key(self, event) -> None:  # noqa: ANN001
        if event.key == "escape":
            self.dismiss(None)
