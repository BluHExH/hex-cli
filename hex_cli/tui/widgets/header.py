from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static


class AppHeader(Horizontal):
    """OpenCode session header: `# title` left, tokens · ctx% · cost right."""

    def __init__(self, **kwargs) -> None:  # noqa: ANN003
        super().__init__(id="top-header", **kwargs)

    def compose(self) -> ComposeResult:
        yield Static("", id="hdr-title")
        yield Static("", id="hdr-stats")

    def set_meta(
        self,
        *,
        title: str,
        tokens: int = 0,
        pct: int = 0,
        cost: str = "$0.00",
    ) -> None:
        label = (title[:56] + "…") if len(title) > 57 else title
        self.query_one("#hdr-title", Static).update(f"[bold]# {label}[/]")
        self.query_one("#hdr-stats", Static).update(f"{tokens:,}  {pct}%  ({cost})")
