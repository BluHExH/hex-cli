"""Conversation log: messages, streaming, tool cards, welcome."""

from __future__ import annotations

import time
import uuid
from typing import ClassVar

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Markdown, Static

from hex_cli.tui.state import ChatEntry
from hex_cli.tui.markdown_util import balance_fences_for_preview, is_near_bottom

_msg_counter = 0


def _next_msg_id() -> str:
    global _msg_counter
    _msg_counter += 1
    return f"msg-{_msg_counter}-{uuid.uuid4().hex[:6]}"


class ChatLog(VerticalScroll):
    """Scrollable conversation history with stream + markdown support."""

    BINDINGS: ClassVar[list] = []

    def __init__(self, **kwargs) -> None:
        super().__init__(id="chat-log", **kwargs)
        self._has_welcome = True
        self._tool_cards: dict = {}
        self._stream_widget_id: str | None = None
        self._stream_raw: str = ""
        self._user_pinned_scroll = False

    def compose(self) -> ComposeResult:
        yield Static(
            self._welcome_markup(),
            classes="message message-welcome",
            id="welcome-msg",
            markup=True,
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

    def _dismiss_welcome(self) -> None:
        if not self._has_welcome:
            return
        try:
            self.query_one("#welcome-msg", Static).remove()
        except Exception:
            pass
        self._has_welcome = False

    def _maybe_autoscroll(self) -> None:
        try:
            if self._user_pinned_scroll:
                return
            max_y = self.max_scroll_y
            if is_near_bottom(self.scroll_y, max_y) or max_y <= 0:
                self.scroll_end(animate=False)
        except Exception:
            try:
                self.scroll_end(animate=False)
            except Exception:
                pass

    def on_scroll(self, event) -> None:  # noqa: ANN001
        # If user scrolls up away from bottom, stop forcing follow
        try:
            if self.max_scroll_y - self.scroll_y > 4:
                self._user_pinned_scroll = True
            else:
                self._user_pinned_scroll = False
        except Exception:
            pass

    def append_entry(self, entry: ChatEntry) -> None:
        self._dismiss_welcome()
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

        if entry.kind == "assistant":
            # Header + Markdown body
            header = Static(
                f"[bold #a78bfa]{label}[/]",
                classes=classes + " message-role",
                markup=True,
            )
            body = Markdown(entry.text or "")
            body.add_class("message-md")
            body.id = wid
            self.mount(header)
            self.mount(body)
            self._maybe_autoscroll()
            return

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
        self._maybe_autoscroll()

    def append_tool_card(
        self,
        tool_name: str,
        status: str,
        detail: str = "",
        output: str = "",
        error: str = "",
        card_key: str | None = None,
    ) -> str:
        from hex_cli.tui.widgets.tool_card import ToolCard

        self._dismiss_welcome()
        if not hasattr(self, "_tool_cards") or self._tool_cards is None:
            self._tool_cards = {}

        key = card_key
        if not key:
            for k, card in list(self._tool_cards.items()):
                if card.tool_name == tool_name and getattr(card.state, "value", "") == "running":
                    key = k
                    break
            if not key:
                key = f"{tool_name}-{id(object())}-{int(time.time()*1000)%100000}"

        card = self._tool_cards.get(key)
        if card is None:
            wid = _next_msg_id()
            card = ToolCard(tool_name, detail=detail, card_key=key, id=wid)
            self._tool_cards[key] = card
            self.mount(card)
        card.set_status(status, detail=detail or None, output=output, error=error)
        self._maybe_autoscroll()
        return key

    def begin_assistant_stream(self) -> str:
        """Mount empty assistant Markdown bubble; return widget id."""
        self._dismiss_welcome()
        self._user_pinned_scroll = False
        self._stream_raw = ""
        wid = _next_msg_id()
        header = Static(
            "[bold #a78bfa]HEX[/]  [dim]streaming…[/]",
            classes="message message-assistant message-role",
            markup=True,
            id=f"{wid}-hdr",
        )
        body = Markdown("")
        body.add_class("message-md")
        body.add_class("message-assistant")
        body.id = wid
        self.mount(header)
        self.mount(body)
        self._stream_widget_id = wid
        self._maybe_autoscroll()
        return wid

    def update_message(self, widget_id: str, text: str, kind: str = "assistant") -> None:
        """Update streaming assistant Markdown (one message, many tokens)."""
        self._stream_raw = text
        preview = balance_fences_for_preview(text)
        try:
            w = self.query_one(f"#{widget_id}", Markdown)
            w.update(preview)
        except Exception:
            try:
                w = self.query_one(f"#{widget_id}", Static)
                safe = preview.replace("[", "\\[")
                w.update(f"[bold #a78bfa]HEX[/]\n{safe}")
            except Exception:
                pass
        self._maybe_autoscroll()

    def finalize_stream(self, widget_id: str | None = None, text: str | None = None) -> None:
        """Mark stream complete; render final markdown without artificial fence close if balanced."""
        wid = widget_id or self._stream_widget_id
        raw = text if text is not None else self._stream_raw
        if wid and raw is not None:
            try:
                w = self.query_one(f"#{wid}", Markdown)
                w.update(raw)
            except Exception:
                pass
            try:
                hdr = self.query_one(f"#{wid}-hdr", Static)
                hdr.update("[bold #a78bfa]HEX[/]")
            except Exception:
                pass
        self._stream_widget_id = None
        self._maybe_autoscroll()

    def clear_messages(self, banner: str | None = None) -> None:
        self._tool_cards = {}
        self._stream_widget_id = None
        self._stream_raw = ""
        self._user_pinned_scroll = False
        for child in list(self.children):
            try:
                child.remove()
            except Exception:
                pass
        self._has_welcome = True
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
