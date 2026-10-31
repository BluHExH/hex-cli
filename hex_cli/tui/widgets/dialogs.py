"""Modal dialogs: help, model/provider picker, permission, confirmation."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, ListItem, ListView, Static


class HelpDialog(ModalScreen[None]):
    """Keyboard shortcuts and usage help."""

    BINDINGS = [("escape", "dismiss", "Close"), ("ctrl+h", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Label("HEX Help", classes="dialog-title")
            yield Static(
                "[bold]Shortcuts[/bold]\n"
                "  Ctrl+C / Ctrl+Q   Quit\n"
                "  Ctrl+L           Clear conversation\n"
                "  Ctrl+N           New session (placeholder)\n"
                "  Ctrl+P           Provider / model picker\n"
                "  Ctrl+B           Toggle sidebar\n"
                "  Ctrl+H           This help\n"
                "  Escape           Close dialog\n"
                "  Enter            Submit prompt\n"
                "  Ctrl+J           Newline in prompt\n\n"
                "[bold]Slash commands[/bold] (type in prompt)\n"
                "  /help  /exit  /clear  /status\n"
                "  /model <id>   /provider <name>\n\n"
                "[bold]Tips[/bold]\n"
                "  • File writes and shell commands require approval.\n"
                "  • Use OpenRouter :free models for $0 usage.\n"
                "  • Run `hex doctor` outside the TUI for diagnostics.\n",
                classes="dialog-body",
                markup=True,
            )
            with Horizontal(classes="dialog-buttons"):
                yield Button("Close", variant="primary", id="btn-close")

    @on(Button.Pressed, "#btn-close")
    def close(self) -> None:
        self.dismiss()


class SelectDialog(ModalScreen[str | None]):
    """Generic list picker — returns selected string or None."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("enter", "choose", "Select"),
    ]

    def __init__(self, title: str, options: list[str], current: str = "") -> None:
        super().__init__()
        self.title_text = title
        self.options = options
        self.current = current

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Label(self.title_text, classes="dialog-title")
            items = [
                ListItem(Label(opt + ("  ←" if opt == self.current else "")), id=f"opt-{i}")
                for i, opt in enumerate(self.options)
            ]
            yield ListView(*items, id="select-list", classes="dialog-list")
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="btn-cancel")
                yield Button("Select", variant="primary", id="btn-ok")

    def on_mount(self) -> None:
        try:
            lv = self.query_one("#select-list", ListView)
            if self.current in self.options:
                lv.index = self.options.index(self.current)
            lv.focus()
        except Exception:
            pass

    @on(Button.Pressed, "#btn-cancel")
    def cancel_btn(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#btn-ok")
    def ok_btn(self) -> None:
        self.action_choose()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_choose(self) -> None:
        try:
            lv = self.query_one("#select-list", ListView)
            idx = lv.index
            if idx is not None and 0 <= idx < len(self.options):
                self.dismiss(self.options[idx])
                return
        except Exception:
            pass
        self.dismiss(None)

    @on(ListView.Selected)
    def on_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self.options):
            self.dismiss(self.options[idx])


class PermissionDialog(ModalScreen[bool]):
    """Ask user to approve a tool action."""

    BINDINGS = [
        ("escape", "deny", "Deny"),
        ("y", "allow", "Allow"),
        ("n", "deny", "Deny"),
    ]

    def __init__(
        self,
        action: str,
        description: str,
        path: str = "",
        detail: str = "",
        high_impact: bool = False,
    ) -> None:
        super().__init__()
        self.action = action
        self.description = description
        self.path = path
        self.detail = detail
        self.high_impact = high_impact

    def compose(self) -> ComposeResult:
        title = "HIGH-IMPACT ACTION" if self.high_impact else "Permission required"
        body = f"[bold]{self.action}[/bold]\n{self.description}\n"
        if self.path:
            body += f"\nPath: {self.path}\n"
        if self.detail:
            d = self.detail if len(self.detail) < 1200 else self.detail[:1200] + "\n…(truncated)"
            body += f"\n{d}"
        with Vertical(classes="dialog"):
            yield Label(title, classes="dialog-title")
            yield Static(body, classes="dialog-body", markup=True)
            with Horizontal(classes="dialog-buttons"):
                yield Button("Deny (N)", id="btn-deny")
                yield Button(
                    "Allow (Y)",
                    variant="error" if self.high_impact else "primary",
                    id="btn-allow",
                )

    @on(Button.Pressed, "#btn-allow")
    def allow_btn(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#btn-deny")
    def deny_btn(self) -> None:
        self.dismiss(False)

    def action_allow(self) -> None:
        self.dismiss(True)

    def action_deny(self) -> None:
        self.dismiss(False)


class ConfirmDialog(ModalScreen[bool]):
    """Simple yes/no confirmation."""

    BINDINGS = [("escape", "no", "No"), ("y", "yes", "Yes"), ("n", "no", "No")]

    def __init__(self, message: str, title: str = "Confirm") -> None:
        super().__init__()
        self.message = message
        self.title_text = title

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Label(self.title_text, classes="dialog-title")
            yield Static(self.message, classes="dialog-body")
            with Horizontal(classes="dialog-buttons"):
                yield Button("No", id="btn-no")
                yield Button("Yes", variant="primary", id="btn-yes")

    @on(Button.Pressed, "#btn-yes")
    def yes_btn(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#btn-no")
    def no_btn(self) -> None:
        self.dismiss(False)

    def action_yes(self) -> None:
        self.dismiss(True)

    def action_no(self) -> None:
        self.dismiss(False)
