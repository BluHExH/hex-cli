"""Terminal UI for HEX CLI using Rich."""

from __future__ import annotations

import sys
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from hex_cli import __version__
from hex_cli.permissions import PermissionRequest

HEX_THEME = Theme(
    {
        "info": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "bold red",
        "accent": "bold magenta",
        "muted": "dim",
        "path": "bold blue",
        "tool": "bold cyan",
    }
)

console = Console(theme=HEX_THEME, highlight=False)


def print_banner(
    project_path: str,
    provider: str,
    model: str,
) -> None:
    """Print the HEX CLI startup banner."""
    banner = Text()
    banner.append("  ██╗  ██╗███████╗██╗  ██╗\n", style="bold magenta")
    banner.append("  ██║  ██║██╔════╝╚██╗██╔╝\n", style="bold magenta")
    banner.append("  ███████║█████╗   ╚███╔╝ \n", style="bold magenta")
    banner.append("  ██╔══██║██╔══╝   ██╔██╗ \n", style="bold magenta")
    banner.append("  ██║  ██║███████╗██╔╝ ██╗\n", style="bold magenta")
    banner.append("  ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝\n", style="bold magenta")
    banner.append(f"  HEX CLI v{__version__}  —  AI Coding Agent\n", style="bold white")

    info = Table.grid(padding=(0, 2))
    info.add_column(style="muted")
    info.add_column()
    info.add_row("Project", f"[path]{project_path}[/path]")
    info.add_row("Provider", f"[accent]{provider}[/accent]")
    info.add_row("Model", f"[accent]{model}[/accent]")
    info.add_row("Help", "[muted]type /help  ·  /exit to quit[/muted]")

    console.print(Panel(banner, border_style="magenta", padding=(0, 1)))
    console.print(info)
    console.print()


def print_version() -> None:
    console.print(f"[accent]HEX CLI[/accent] version [bold]{__version__}[/bold]")


def print_success(msg: str) -> None:
    console.print(f"[success]✓[/success] {msg}")


def print_error(msg: str) -> None:
    console.print(f"[error]✗[/error] {msg}")


def print_warning(msg: str) -> None:
    console.print(f"[warning]![/warning] {msg}")


def print_info(msg: str) -> None:
    console.print(f"[info]•[/info] {msg}")


def print_tool_status(tool_name: str, status: str, detail: str = "") -> None:
    icon = {
        "running": "[tool]⟳[/tool]",
        "ok": "[success]✓[/success]",
        "error": "[error]✗[/error]",
        "skipped": "[warning]⊘[/warning]",
    }.get(status, "•")
    line = f"  {icon} [tool]{tool_name}[/tool]"
    if detail:
        line += f"  [muted]{detail}[/muted]"
    console.print(line)


def print_assistant(text: str) -> None:
    """Render assistant response (supports light markdown)."""
    try:
        console.print(Markdown(text))
    except Exception:
        console.print(text)


def print_diff(diff_text: str, title: str = "Diff") -> None:
    if not diff_text.strip():
        console.print("[muted](no changes)[/muted]")
        return
    syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title=title, border_style="cyan"))


def print_code(code: str, lexer: str = "python", title: str | None = None) -> None:
    syntax = Syntax(code, lexer, theme="monokai", line_numbers=True)
    if title:
        console.print(Panel(syntax, title=title, border_style="blue"))
    else:
        console.print(syntax)


def ask_permission(request: PermissionRequest) -> bool:
    """Interactive permission prompt. Returns True if user approves."""
    console.print()
    style = "bold red" if request.high_impact else "bold yellow"
    label = "HIGH-IMPACT ACTION" if request.high_impact else "Permission required"

    lines = [f"[{style}]{label}[/{style}]"]
    lines.append(f"  Action : [tool]{request.action.value}[/tool]")
    lines.append(f"  Detail : {request.description}")
    if request.path:
        lines.append(f"  Path   : [path]{request.path}[/path]")
    if request.detail and request.action.value in (
        "run_command",
        "modify_file",
        "create_file",
        "git_commit",
    ):
        detail = request.detail
        if len(detail) > 1500:
            detail = detail[:1500] + "\n… (truncated)"
        if request.action.value == "modify_file" or "diff" in request.description.lower():
            console.print("\n".join(lines))
            print_diff(request.detail, title="Proposed change")
        else:
            lines.append(f"  Content:\n[muted]{detail}[/muted]")
            console.print("\n".join(lines))
    else:
        console.print("\n".join(lines))

    if request.high_impact:
        return Confirm.ask(
            "[bold red]This is a high-impact action. Type 'y' to confirm[/bold red]",
            default=False,
        )
    return Confirm.ask("Allow this action?", default=False)


def prompt_user(default: str = "") -> str:
    """Read a line from the user at the interactive prompt."""
    try:
        return Prompt.ask("[bold magenta]hex >[/bold magenta]", default=default).strip()
    except (EOFError, KeyboardInterrupt):
        console.print()
        return "/exit"


def spinner(message: str = "Thinking…"):
    """Context manager that shows a spinner."""
    return Progress(
        SpinnerColumn(style="magenta"),
        TextColumn("[magenta]{task.description}[/magenta]"),
        console=console,
        transient=True,
    )


def print_table(headers: list[str], rows: list[list[str]], title: str | None = None) -> None:
    table = Table(title=title, show_header=True, header_style="bold cyan")
    for h in headers:
        table.add_column(h)
    for row in rows:
        table.add_row(*[str(c) for c in row])
    console.print(table)


def print_help() -> None:
    help_text = """
[bold accent]HEX CLI Commands[/bold accent]

  [bold]/help[/bold]              Show this help
  [bold]/exit[/bold], [bold]/quit[/bold]     Exit the session
  [bold]/clear[/bold]             Clear conversation context
  [bold]/status[/bold]            Show project & provider status
  [bold]/model[/bold]             Show or switch model
  [bold]/provider[/bold]          Show or switch provider
  [bold]/permissions[/bold]       Show current permission settings

[bold accent]CLI Commands[/bold accent]

  [bold]hex[/bold]                 Start interactive coding agent
  [bold]hex --version[/bold]       Show version
  [bold]hex --help[/bold]          Show CLI help
  [bold]hex doctor[/bold]           Diagnose environment & config
  [bold]hex config[/bold]           View / edit configuration
  [bold]hex models[/bold]           List available models
  [bold]hex model <name>[/bold]     Set default model
  [bold]hex init[/bold]             Initialise HEX config in ~/.hex

[bold accent]Tips[/bold accent]

  • Describe coding tasks in natural language.
  • The agent will ask before modifying files or running commands.
  • Keep sensitive keys in environment variables or ~/.hex/.env
"""
    console.print(help_text)
