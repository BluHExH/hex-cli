"""Main conversation panel."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from hex_cli.tui.state import ChatEntry


class ChatLog(VerticalScroll):
    """Scrollable conversation history."""

    def __init__(self, **kwargs) -> None:
        super().__init__(id="chat-log", **kwargs)
        self._count = 0

    def compose(self) -> ComposeResult:
        yield Static(
            "[dim]Welcome to HEX. Type a coding task below, or press Ctrl+H for help.[/dim]",
            classes="message message-system",
            id="welcome-msg",
        )

    def append_entry(self, entry: ChatEntry) -> None:
        self._count += 1
        wid = f"msg-{self._count}"
        classes = f"message message-{entry.kind}"
        label = {
            "user": "You",
            "assistant": "HEX",
            "tool": "Tool",
            "error": "Error",
            "system": "System",
            "status": "…",
        }.get(entry.kind, entry.kind)

        body = entry.text
        if entry.kind == "tool":
            status = entry.meta.get("status", "")
            icon = {"running": "⟳", "ok": "✓", "error": "✗", "skipped": "⊘"}.get(status, "•")
            body = f"{icon} {entry.text}"

        # Escape Rich markup edge cases lightly
        safe = body.replace("[", "\\[")
        widget = Static(
            f"[bold]{label}[/bold]\n{safe}",
            classes=classes,
            id=wid,
            markup=True,
        )
        self.mount(widget)
        self.scroll_end(animate=False)

    def clear_messages(self) -> None:
        for child in list(self.children):
            child.remove()
        self._count = 0
        self.mount(
            Static(
                "[dim]Conversation cleared. Ask HEX something…[/dim]",
                classes="message message-system",
            )
        )
