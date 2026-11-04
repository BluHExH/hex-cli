from __future__ import annotations

from textual.widgets import Static


class StatusBar(Static):
    """OpenCode-style hint line: dots + esc interrupt · tab agents · ctrl+p commands."""

    def __init__(self, **kwargs) -> None:  # noqa: ANN003
        super().__init__(id="bottom-status", **kwargs)

    def set_status(self, *, ready: bool, model: str = "", workspace: str = "") -> None:
        left = "[dim]· · · · · ·[/]  esc interrupt" if not ready else "[dim]· · · · · ·[/]"
        self.update(
            f"{left}    "
            f"[dim]tab[/] agents   [dim]ctrl+p[/] commands   [dim]ctrl+n[/] new session"
        )
