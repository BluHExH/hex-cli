from __future__ import annotations

from textual.containers import VerticalScroll
from textual.widgets import Static


class LeftRail(VerticalScroll):
    """Reference left column: Session, Workspace, Context, Tools, Permissions, Recent, Help."""

    def __init__(self) -> None:
        super().__init__(id="left-rail")
        self._collapsed = False

    def compose(self):
        yield Static(id="left-body")

    def set_data(
        self,
        *,
        workspace: str,
        context_chars: int = 0,
        context_max: int = 32_000,
        tool_count: int = 0,
        permission_mode: str = "prompt",
        recent_files: list[str] | None = None,
    ) -> None:
        # Reference shows 25% · 8.2K / 32K style context
        max_c = max(1, context_max)
        pct = min(100, int(100 * context_chars / max_c))
        used_k = f"{context_chars / 1000:.1f}K"
        max_k = f"{max_c / 1000:.0f}K"
        filled = max(0, min(12, round(pct / 100 * 12)))
        bar = "[#7c6cf0]" + "━" * filled + "[/][dim]" + "━" * (12 - filled) + "[/]"
        files = recent_files or []
        fl = "\n".join(f"[dim]  📄 [/]{f}" for f in files[:5]) or "[dim]  —[/]"
        if permission_mode == "allow":
            perm = "[green]●[/] Auto-approve: All"
        elif permission_mode == "deny":
            perm = "[red]●[/] Deny all"
        else:
            perm = "[green]●[/] Auto-approve: Read"
        ws = workspace if len(workspace) < 28 else "…" + workspace[-25:]
        self.query_one("#left-body", Static).update(
            "\n".join(
                [
                    "[bold]Session[/]                    [dim]↦[/]",
                    "[dim]  ⧉[/] New Session           [dim]Ctrl+N[/]",
                    "[dim]  ⇄[/] Switch Session        [dim]Ctrl+⇧+S[/]",
                    "[dim]  ☰[/] Manage Sessions",
                    "",
                    "[bold]Workspace[/]                 [dim]▾[/]",
                    f"[dim]  📁 Current Directory[/]",
                    f"  [dim]{ws}[/]",
                    "",
                    "[bold]Context[/]",
                    f"  {pct}%  ·  {used_k} / {max_k}",
                    f"  {bar}",
                    "",
                    "[bold]Tools[/]                     [dim]▾[/]",
                    f"[dim]  🔧[/] {tool_count} tools available",
                    "",
                    "[bold]Permissions[/]",
                    f"  {perm}",
                    "",
                    "[bold]Recent Files[/]",
                    fl,
                    "",
                    "[dim]  ? Help      ⚙ Settings[/]",
                ]
            )
        )

    def toggle(self) -> None:
        self._collapsed = not self._collapsed
        self.set_class(self._collapsed, "collapsed")
        self.display = not self._collapsed
