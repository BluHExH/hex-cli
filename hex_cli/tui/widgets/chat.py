"""Main conversation panel — OpenCode-style message layout with unique IDs."""

from __future__ import annotations

import itertools
import uuid
from typing import ClassVar

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from hex_cli.tui.state import ChatEntry

_MSG_SEQ = itertools.count(1)


def _next_msg_id() -> str:
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
        lines = [
            "",
            "[bold #a78bfa]██╗  ██╗███████╗██╗  ██╗[/]",
            "[bold #a78bfa]██║  ██║██╔════╝╚██╗██╔╝[/]",
            "[bold #a78bfa]███████║█████╗   ╚███╔╝[/]",
            "[bold #a78bfa]██╔══██║██╔══╝   ██╔██╗[/]",
            "[bold #a78bfa]██║  ██║███████╗██╔╝ ██╗[/]",
            "[bold #a78bfa]╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝[/]",
            "",
            "[bold]Your AI Coding Workspace[/]",
            "[dim]Build. Create. Explore.[/]",
            "",
            "[dim]Powered by HEX  ·  By NeonBuild[/]",
            "",
            "[dim]Enter a task below  ·  /provider  ·  /models  ·  /help[/]",
        ]
        return "\n".join(lines)

    def append_entry(self, entry: ChatEntry) -> None:
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
            icon = {
                "running": "⟳",
                "ok": "✓",
                "error": "✗",
                "skipped": "⊘",
                "denied": "⊘",
                "cancelled": "–",
            }.get(status, "•")
            body = f"{icon}  {entry.text}"

        safe = body.replace("[", "\\[")
        header_color = {
            "user": "#58a6ff",
            "assistant": "#a78bfa",
            "tool": "#d29922",
            "error": "#f85149",
            "system": "#7d8590",
            "status": "#6e7681",
        }.get(entry.kind, "#e6edf3")

        widget = Static(
            f"[bold {header_color}]{label}[/]\n{safe}",
            classes=classes,
            id=wid,
            markup=True,
        )
        self.mount(widget)
        self.scroll_end(animate=False)



    def append_tool_card(
        self,
        tool_name: str,
        status: str,
        detail: str = "",
        output: str = "",
        error: str = "",
        card_key: str | None = None,
    ) -> str:
        """Create or update an expandable ToolCard for a real tool event."""
        from hex_cli.tui.widgets.tool_card import ToolCard, status_from_string

        if self._has_welcome:
            try:
                self.query_one("#welcome-msg").remove()
            except Exception:
                pass
            self._has_welcome = False

        if not hasattr(self, "_tool_cards"):
            self._tool_cards: dict[str, ToolCard] = {}

        # Reuse running card for same tool+detail while still running
        key = card_key
        if not key:
            # Prefer matching an existing RUNNING card for this tool
            for k, card in list(self._tool_cards.items()):
                if card.tool_name == tool_name and card.state.value == "running":
                    key = k
                    break
            if not key:
                key = f"{tool_name}-{id(object())}-{int(__import__('time').time()*1000)%100000}"

        card = self._tool_cards.get(key)
        if card is None:
            wid = _next_msg_id()
            card = ToolCard(tool_name, detail=detail, card_key=key, id=wid)
            self._tool_cards[key] = card
            self.mount(card)
            self.scroll_end(animate=False)
        card.set_status(status, detail=detail or None, output=output, error=error)
        self.scroll_end(animate=False)
        return key


    def update_message(self, widget_id: str, text: str, kind: str = "assistant") -> None:
        """Update an existing message widget (streaming)."""
        try:
            w = self.query_one(f"#{widget_id}", Static)
            label = {"assistant": "HEX", "status": "…", "tool": "Tool"}.get(kind, kind)
            color = {"assistant": "#a78bfa", "status": "#6e7681", "tool": "#d29922"}.get(kind, "#e6edf3")
            safe = text.replace("[", "\\[")
            w.update(f"[bold {color}]{label}[/]\n{safe}")
            self.scroll_end(animate=False)
        except Exception:
            pass

    def begin_assistant_stream(self) -> str:
        """Mount an empty assistant bubble; return widget id for streaming updates."""
        if self._has_welcome:
            try:
                self.query_one("#welcome-msg").remove()
            except Exception:
                pass
            self._has_welcome = False
        wid = _next_msg_id()
        widget = Static(
            "[bold #a78bfa]HEX[/]\n[dim]…[/]",
            classes="message message-assistant",
            id=wid,
            markup=True,
        )
        self.mount(widget)
        self.scroll_end(animate=False)
        return wid

    def clear_messages(self, *, banner: str | None = None) -> None:
        self._tool_cards = {}
        try:
            self.remove_children()
        except Exception:
            for child in list(self.children):
                try:
                    child.remove()
                except Exception:
                    pass

        text = banner if banner is not None else self._welcome_markup()
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
