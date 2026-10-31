"""Main conversation panel with unique message widget IDs."""

from __future__ import annotations

import itertools
import uuid
from typing import ClassVar

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from hex_cli.tui.state import ChatEntry

# Process-wide monotonic counter — never resets across clear/new-session.
_MSG_SEQ = itertools.count(1)


def _next_msg_id() -> str:
    """Return a globally unique widget id for a chat message."""
    return f"msg-{next(_MSG_SEQ)}-{uuid.uuid4().hex[:8]}"


class ChatLog(VerticalScroll):
    """Scrollable conversation history."""

    BINDINGS: ClassVar[list] = []

    def __init__(self, **kwargs) -> None:
        super().__init__(id="chat-log", **kwargs)
        self._has_welcome = True

    def compose(self) -> ComposeResult:
        yield Static(
            self._welcome_markup(),
            classes="message message-welcome",
            id="welcome-msg",
        )

    @staticmethod
    def _welcome_markup() -> str:
        return (
            "[bold #c084fc]Welcome to HEX[/]\n"
            "[dim]Describe a coding task, or type [bold]/[/] for commands.\n"
            "Ctrl+H help · Ctrl+P models · Ctrl+N new session[/]"
        )

    def append_entry(self, entry: ChatEntry) -> None:
        # Remove welcome banner on first real message
        if self._has_welcome:
            try:
                w = self.query_one("#welcome-msg", Static)
                w.remove()
            except Exception:
                pass
            self._has_welcome = False

        wid = _next_msg_id()
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
            icon = {"running": "⟳", "ok": "✓", "error": "✗", "skipped": "⊘"}.get(
                status, "•"
            )
            body = f"{icon} {entry.text}"

        # Escape markup brackets so user content cannot break Rich markup
        safe = body.replace("[", "\\[")
        header_color = {
            "user": "#58a6ff",
            "assistant": "#c084fc",
            "tool": "#d29922",
            "error": "#f85149",
            "system": "#8b949e",
            "status": "#8b949e",
        }.get(entry.kind, "#e6edf3")

        widget = Static(
            f"[bold {header_color}]{label}[/]\n{safe}",
            classes=classes,
            id=wid,
            markup=True,
        )
        self.mount(widget)
        self.scroll_end(animate=False)

    def clear_messages(self, *, banner: str | None = None) -> None:
        """Remove all message widgets and show a welcome/cleared banner.

        Uses remove_children() so Textual releases IDs before new widgets mount.
        Message IDs are never reused (global monotonic + uuid).
        """
        # Synchronous bulk removal — avoids ID collisions with deferred remove()
        try:
            self.remove_children()
        except Exception:
            for child in list(self.children):
                try:
                    child.remove()
                except Exception:
                    pass

        text = banner if banner is not None else self._welcome_markup()
        # Banner gets a unique id each time as well
        banner_id = f"welcome-{uuid.uuid4().hex[:8]}"
        self.mount(
            Static(
                text,
                classes="message message-welcome",
                id=banner_id,
                markup=True,
            )
        )
        self._has_welcome = True
        self.scroll_home(animate=False)
