from __future__ import annotations

from textual.widgets import RichLog


class ConversationTimeline(RichLog):
    """Conversation stream with structured message styles."""

    def __init__(self, **kwargs) -> None:
        super().__init__(
            id="timeline",
            markup=True,
            wrap=True,
            highlight=True,
            max_lines=4000,
            **kwargs,
        )

    def add_user(self, text: str) -> None:
        self.write(f"[bold #7dd3fc]You[/]")
        self.write(text)
        self.write("")

    def add_assistant(self, text: str, *, cancelled: bool = False) -> None:
        label = "[bold #fbbf24]HEX[/] [dim]cancelled[/]" if cancelled else "[bold #a78bfa]HEX[/]"
        self.write(label)
        self.write(text)
        self.write("")

    def add_tool(self, name: str, ok: bool, detail: str = "") -> None:
        status = "[green]ok[/]" if ok else "[red]err[/]"
        self.write(f"[#fbbf24]▸ tool[/] [bold]{name}[/] {status}")
        if detail:
            clipped = detail if len(detail) <= 1200 else detail[:1200] + "\n…"
            for line in clipped.splitlines()[:40]:
                self.write(f"  [dim]{line}[/]")
        self.write("")

    def add_error(self, text: str) -> None:
        self.write(f"[bold red]Error[/] {text}")
        self.write("")

    def add_system(self, text: str) -> None:
        self.write(f"[dim]{text}[/]")
