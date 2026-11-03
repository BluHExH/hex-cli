from __future__ import annotations

from textual.widgets import RichLog


class ConversationTimeline(RichLog):
    def __init__(self) -> None:
        super().__init__(id="timeline", markup=True, wrap=True, highlight=True, max_lines=5000)

    def show_welcome(self, model: str) -> None:
        self.write("")
        self.write("[bold #c4b5fd]✦  Welcome to HEX[/]")
        self.write("[dim]Your AI coding agent, right in your terminal.[/]")
        self.write(f"[dim]Model:[/] {model}")
        self.write("")

    def add_user(self, text: str, time_label: str = "") -> None:
        t = f"  [dim]{time_label}[/]" if time_label else ""
        self.write(f"[bold #9ecbff]You[/]{t}")
        self.write(text)
        self.write("")

    def add_assistant(self, text: str, time_label: str = "", cancelled: bool = False) -> None:
        t = f"  [dim]{time_label}[/]" if time_label else ""
        label = "[bold #fbbf24]HEX[/] [dim]cancelled[/]" if cancelled else "[bold #a78bfa]HEX[/]"
        self.write(f"{label}{t}")
        self.write(text)
        self.write("")

    def add_planning(self, steps: int, summary: str) -> None:
        self.write(f"[green]✓[/] [bold]Planning[/] [dim]· {steps} steps[/]")
        if summary:
            self.write(f"[dim]{summary}[/]")
        self.write("")

    def add_tool_card(self, kind: str, target: str, ok: bool, duration: str = "", preview: str = "") -> None:
        status = "[green]Completed[/]" if ok else "[red]Failed[/]"
        dur = f" · {duration}" if duration else ""
        self.write(f"┌─ [bold]{kind}[/] [dim]{target}[/]  {status}{dur}")
        if preview:
            for line in preview.splitlines()[:6]:
                self.write(f"│  [dim]{line}[/]")
        self.write("└─")
        self.write("")

    def add_success(self, text: str) -> None:
        self.write(f"[green]✓[/] {text}")
        self.write("")

    def add_error(self, text: str) -> None:
        self.write(f"[bold red]Error[/] {text}")
        self.write("")

    def add_system(self, text: str) -> None:
        self.write(f"[dim]{text}[/]")
