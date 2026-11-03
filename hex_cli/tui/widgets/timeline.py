from __future__ import annotations

from textual.widgets import RichLog


class ConversationTimeline(RichLog):
    """Center conversation matching reference hierarchy: welcome, You, agent, tool cards."""

    def __init__(self) -> None:
        super().__init__(id="timeline", markup=True, wrap=True, highlight=True, max_lines=6000)

    def show_welcome(self, model: str) -> None:
        self.write("╭────────────────────────────────────────────────────────────╮")
        self.write("│  [bold #c4b5fd]✦  Welcome to HEX[/]                                      │")
        self.write("│  [dim]Your AI coding agent, right in your terminal.[/]           │")
        self.write(f"│  [dim]                                          [/][green]●[/] {model[:20]:<20} │")
        self.write("╰────────────────────────────────────────────────────────────╯")
        self.write("")

    def add_user(self, text: str, time_label: str = "") -> None:
        t = f"  [dim]{time_label}[/]" if time_label else ""
        self.write(f"[bold #a8c7fa]● You[/]{t}")
        self.write(f"{text}")
        self.write("")

    def add_assistant(self, text: str, time_label: str = "", cancelled: bool = False) -> None:
        t = f"  [dim]{time_label}[/]" if time_label else ""
        if cancelled:
            self.write(f"[bold #e6c07b]HEX[/] [dim]cancelled[/]{t}")
        else:
            self.write(f"[bold #a78bfa]◆ HEX[/]{t}")
        self.write(text)
        self.write("")

    def add_planning(self, steps: int, summary: str) -> None:
        self.write(f"  [green]✓[/] [bold]Planning[/]  [dim]· {steps} steps[/]")
        if summary:
            self.write(f"  {summary}")
        self.write("")

    def add_tool_card(self, kind: str, target: str, ok: bool, duration: str = "", preview: str = "") -> None:
        status = "[green]✓ Completed[/]" if ok else "[red]✗ Failed[/]"
        dur = f"  [dim]· {duration}[/]" if duration else ""
        self.write(f"  ╭─ [bold]{kind}[/]  [dim]{target}[/]".ljust(40) + f"  {status}{dur}")
        if preview:
            for i, line in enumerate(preview.splitlines()[:5], 1):
                self.write(f"  │ [dim]{i:>2}[/] {line[:70]}")
        self.write("  ╰─")
        self.write("")

    def add_success(self, text: str) -> None:
        self.write(f"  [green]✓[/] {text}")
        self.write("")

    def add_error(self, text: str) -> None:
        self.write(f"[bold red]Error[/] {text}")
        self.write("")

    def add_system(self, text: str) -> None:
        self.write(f"[dim]{text}[/]")
