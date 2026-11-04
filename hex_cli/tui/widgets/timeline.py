from __future__ import annotations

from textual.widgets import RichLog

from hex_cli.providers.base import ChatMessage

# OpenCode v2 palette: near-black canvas, blue accent for user blocks / mode,
# grey tool lines, muted notes.
_USER_BG = "on #121318"
_BAR = f"[{_USER_BG}][bold #4d9eff]▌[/][/] "

TOOL_LABELS = {
    "read_file": "Read",
    "write_file": "Write",
    "list_dir": "Glob",
    "search_files": "Grep",
    "run_shell": "Bash",
}

RUNNING = "~"


def tool_label(name: str) -> str:
    return TOOL_LABELS.get(name, name or "Tool")


def tool_arg(name: str, content: str, meta: dict[str, str] | None = None) -> str:
    """Short argument display, e.g. Glob "src" / Bash "npm test"."""
    meta = meta or {}
    if name == "run_shell":
        return f'"{meta.get("command") or content[:40]}"'
    path = meta.get("path") or (content.splitlines()[0][:40] if content.strip() else "")
    if name == "search_files":
        return f'"{path}"'
    return f'"{path}"' if path else '""'


def tool_paren(name: str, ok: bool, out: str) -> str:
    """OpenCode-style '(* N matches)' summary derived from real output."""
    if not ok or not out:
        return ""
    def _count(label: str, n: int) -> str:
        return f"({n} {label}{'' if n == 1 else 's'})"

    if name == "list_dir":
        n = len([ln for ln in out.splitlines() if ln != "(empty)"])
        return _count("entry", n)
    if name == "search_files":
        return _count("match", len(out.splitlines()))
    if name == "write_file":
        i = out.find("(")
        j = out.find(")", i + 1) if i != -1 else -1
        return out[i : j + 1] if i != -1 and j != -1 else ""
    if name == "read_file":
        return ""
    return ""


class ConversationTimeline(RichLog):
    """OpenCode-style conversation: blue-bar user blocks, grey tool lines, plain replies."""

    def __init__(self) -> None:
        super().__init__(id="timeline", markup=True, wrap=True, highlight=False, max_lines=8000)

    # -- lifecycle -------------------------------------------------------
    def reset(self, tip: str = "") -> None:
        self.clear()
        if tip:
            self.write(f"[dim]{tip}[/]")

    # -- blocks ----------------------------------------------------------
    def add_tip(self, text: str) -> None:
        self.write(f"[dim]{text}[/]")

    def add_user(self, text: str) -> None:
        for line in text.splitlines() or [""]:
            self.write(f"{_BAR}{line}")
        self.write("")

    def add_note(self, text: str) -> None:
        self.write(f"[dim]· {text}[/]")

    def add_error(self, text: str) -> None:
        self.write(f"[bold #e05c5c]! {text}[/]")
        self.write("")

    def add_tool(
        self,
        name: str,
        ok: bool,
        duration: float | None = None,
        out: str = "",
        meta: dict[str, str] | None = None,
    ) -> None:
        label = tool_label(name)
        arg = tool_arg(name, "", meta)
        if ok:
            paren = tool_paren(name, ok, out)
            suffix = f" {paren}" if paren else ""
            self.write(f"[dim]* {label} {arg}{suffix}[/]")
            if name == "run_shell" and out:
                for line in out.splitlines()[:3]:
                    self.write(f"[dim]    {line[:90]}[/]")
        else:
            detail = (out or "").splitlines()[:1]
            msg = detail[0] if detail else "failed"
            self.write(f"[bold #e05c5c]! {label} {arg}[/][dim] {msg[:80]}[/]")
        self.write("")

    def add_assistant(self, text: str, cancelled: bool = False) -> None:
        self.write(text or "[dim]No response[/]")
        if cancelled:
            self.write("[dim]· interrupted[/]")
        self.write("")

    # -- replay ----------------------------------------------------------
    def replay(self, history: list[ChatMessage], details: bool = True) -> None:
        self.clear()
        for msg in history:
            meta = getattr(msg, "meta", None) or {}
            if msg.role == "user":
                self.add_user(msg.content)
            elif msg.role == "tool":
                if details:
                    self.add_tool(msg.name or "", ok=bool(msg.content and not _is_error(msg.content)), out=msg.content, meta=meta)
            elif msg.role == "assistant":
                self.add_assistant(msg.content)
            elif msg.role == "system":
                self.add_note(msg.content)


def _is_error(content: str) -> bool:
    return content.startswith("permission denied") or content.startswith("unknown tool")
