"""Stage 2 dialogs: connect provider, model browser, providers list, settings."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView, Static

from hex_cli.providers.catalog import ModelInfo
from hex_cli.providers.registry import ProviderSpec


class ConnectProviderDialog(ModalScreen[tuple[str, str] | None]):
    """Pick a provider, then enter an API key. Returns (provider_id, api_key) or None."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, specs: list[ProviderSpec], connected: set[str] | None = None) -> None:
        super().__init__()
        self.specs = specs
        self.connected = connected or set()
        self._selected: ProviderSpec | None = None
        self._phase = "pick"  # pick | key

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Label("Connect Provider", classes="dialog-title")
            yield Static(
                "Select a provider, then enter an API key.\n"
                "Keys are stored in ~/.hex/credentials.json (not committed).",
                classes="dialog-body",
            )
            items = []
            for i, s in enumerate(self.specs):
                mark = " ✓" if s.id in self.connected else ""
                req = "" if s.requires_key else " (no key required)"
                items.append(
                    ListItem(
                        Label(f"{s.display_name}{mark}{req}  — {s.notes[:40]}"),
                        id=f"prov-{i}",
                    )
                )
            yield ListView(*items, id="prov-list", classes="dialog-list")
            yield Input(
                placeholder="Paste API key here (hidden after save)",
                password=True,
                id="api-key-input",
            )
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="btn-cancel")
                yield Button("Connect", variant="primary", id="btn-connect")

    def on_mount(self) -> None:
        try:
            self.query_one("#prov-list", ListView).focus()
        except Exception:
            pass

    @on(ListView.Selected)
    def on_pick(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self.specs):
            self._selected = self.specs[idx]

    @on(Button.Pressed, "#btn-cancel")
    def cancel_btn(self) -> None:
        self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#btn-connect")
    def connect_btn(self) -> None:
        if self._selected is None:
            try:
                lv = self.query_one("#prov-list", ListView)
                idx = lv.index
                if idx is not None and 0 <= idx < len(self.specs):
                    self._selected = self.specs[idx]
            except Exception:
                pass
        if self._selected is None:
            return
        key_widget = self.query_one("#api-key-input", Input)
        key = key_widget.value.strip()
        if self._selected.requires_key and not key:
            key_widget.placeholder = "API key required for this provider"
            return
        self.dismiss((self._selected.id, key))


class ModelBrowserDialog(ModalScreen[str | None]):
    """Searchable model list with free/paid labels."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("enter", "choose", "Select"),
        ("f", "toggle_free", "Free only"),
    ]

    def __init__(
        self,
        models: list[ModelInfo],
        current: str = "",
        title: str = "Select Model",
        free_only: bool = False,
    ) -> None:
        super().__init__()
        self.all_models = models
        self.current = current
        self.title_text = title
        self.free_only = free_only
        self._filtered: list[ModelInfo] = []

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Label(self.title_text, classes="dialog-title")
            yield Static(
                "Type to search · F free-only · Enter select · Esc cancel",
                classes="dialog-body",
            )
            yield Input(placeholder="Search models…", id="model-search")
            yield ListView(id="model-list", classes="dialog-list")
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="btn-cancel")
                yield Button("Select", variant="primary", id="btn-ok")

    def on_mount(self) -> None:
        self._apply_filter("")
        try:
            self.query_one("#model-search", Input).focus()
        except Exception:
            pass

    def _apply_filter(self, query: str) -> None:
        q = query.strip().lower()
        models = self.all_models
        if self.free_only:
            models = [m for m in models if m.cost_tier == "free"]
        if q:
            models = [
                m
                for m in models
                if q in m.id.lower() or q in m.name.lower() or q in m.provider.lower()
            ]
        self._filtered = models[:200]
        try:
            lv = self.query_one("#model-list", ListView)
            lv.clear()
            for i, m in enumerate(self._filtered):
                mark = " ←" if m.id == self.current else ""
                lv.append(ListItem(Label(m.label() + mark), id=f"m-{i}"))
        except Exception:
            pass

    @on(Input.Changed, "#model-search")
    def on_search(self, event: Input.Changed) -> None:
        self._apply_filter(event.value)

    def action_toggle_free(self) -> None:
        self.free_only = not self.free_only
        try:
            q = self.query_one("#model-search", Input).value
        except Exception:
            q = ""
        self._apply_filter(q)

    @on(Button.Pressed, "#btn-cancel")
    def cancel_btn(self) -> None:
        self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#btn-ok")
    def ok_btn(self) -> None:
        self.action_choose()

    def action_choose(self) -> None:
        try:
            lv = self.query_one("#model-list", ListView)
            idx = lv.index
            if idx is not None and 0 <= idx < len(self._filtered):
                self.dismiss(self._filtered[idx].id)
                return
        except Exception:
            pass
        self.dismiss(None)

    @on(ListView.Selected)
    def on_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self._filtered):
            self.dismiss(self._filtered[idx].id)


class ProvidersStatusDialog(ModalScreen[None]):
    """Show connected providers."""

    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, lines: list[str]) -> None:
        super().__init__()
        self.lines = lines

    def compose(self) -> ComposeResult:
        body = "\n".join(self.lines) if self.lines else "(no providers connected)"
        with Vertical(classes="dialog"):
            yield Label("Providers", classes="dialog-title")
            yield Static(body, classes="dialog-body")
            with Horizontal(classes="dialog-buttons"):
                yield Button("Close", variant="primary", id="btn-close")

    @on(Button.Pressed, "#btn-close")
    def close(self) -> None:
        self.dismiss()


class SettingsDialog(ModalScreen[None]):
    """Minimal settings overview."""

    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Label("HEX Settings", classes="dialog-title")
            yield Static(self.text, classes="dialog-body")
            with Horizontal(classes="dialog-buttons"):
                yield Button("Close", variant="primary", id="btn-close")

    @on(Button.Pressed, "#btn-close")
    def close(self) -> None:
        self.dismiss()
