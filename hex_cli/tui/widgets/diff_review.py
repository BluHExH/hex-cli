"""Interactive in-chat diff review widget for HEX CLI."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import Button, Static

from hex_cli.changes.tracker import ChangeRecord, ChangeTracker


class DiffAccept(Message):
    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path


class DiffReject(Message):
    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path


class DiffReviewClosed(Message):
    pass


def format_unified_diff_markup(diff: str, max_lines: int = 80) -> str:
    """Colorize unified diff lines for Textual markup."""
    lines = (diff or "").splitlines()
    out: list[str] = []
    shown = 0
    for line in lines:
        if shown >= max_lines:
            out.append(f"[dim]… ({len(lines) - max_lines} more lines)[/]")
            break
        safe = line.replace("[", "\\[")
        if line.startswith("+++") or line.startswith("---"):
            out.append(f"[bold]{safe}[/]")
        elif line.startswith("@@"):
            out.append(f"[cyan]{safe}[/]")
        elif line.startswith("+"):
            out.append(f"[green]{safe}[/]")
        elif line.startswith("-"):
            out.append(f"[red]{safe}[/]")
        else:
            out.append(f"[dim]{safe}[/]")
        shown += 1
    return "\n".join(out) if out else "[dim](empty diff)[/]"


class DiffReviewPanel(Vertical):
    """Navigate pending file changes; accept or reject each path."""

    BINDINGS = [
        ("left", "prev", "Previous"),
        ("right", "next", "Next"),
        ("a", "accept", "Accept"),
        ("r", "reject", "Reject"),
        ("escape", "close", "Close"),
    ]

    def __init__(self, tracker: ChangeTracker, **kwargs) -> None:
        super().__init__(id="diff-review", **kwargs)
        self.tracker = tracker
        self.paths: list[str] = list(tracker.file_paths()) if hasattr(tracker, "file_paths") else []
        if not self.paths:
            # fallback from summary
            self.paths = [f["path"] for f in tracker.summary().get("files", [])]
        self.index = 0
        self.status_note = "Pending review"
        self.can_focus = True

    def compose(self) -> ComposeResult:
        yield Static("", id="diff-header", markup=True)
        with VerticalScroll(id="diff-body"):
            yield Static("", id="diff-content", markup=True)
        with Horizontal(id="diff-actions"):
            yield Button("Accept", id="diff-accept", variant="success")
            yield Button("Reject", id="diff-reject", variant="error")
            yield Button("Prev", id="diff-prev")
            yield Button("Next", id="diff-next")
            yield Button("Close", id="diff-close")
        yield Static("", id="diff-footer", markup=True)

    def on_mount(self) -> None:
        self._refresh()
        self.focus()

    def current_path(self) -> str | None:
        if not self.paths:
            return None
        self.index = max(0, min(self.index, len(self.paths) - 1))
        return self.paths[self.index]

    def _record(self) -> ChangeRecord | None:
        path = self.current_path()
        if not path:
            return None
        if hasattr(self.tracker, "get_latest_for"):
            return self.tracker.get_latest_for(path)
        for r in reversed(self.tracker.records):
            if r.path == path:
                return r
        return None

    def _refresh(self) -> None:
        n = len(self.paths)
        path = self.current_path()
        header = self.query_one("#diff-header", Static)
        content = self.query_one("#diff-content", Static)
        footer = self.query_one("#diff-footer", Static)
        if not path or n == 0:
            header.update("[bold]DIFF REVIEW[/]  — no pending changes")
            content.update("[dim]Nothing to review.[/]")
            footer.update("")
            return
        rec = self._record()
        add = rem = 0
        diff_text = ""
        action = "?"
        if rec:
            add, rem = rec.stats()
            diff_text = rec.unified_diff()
            action = rec.action
        header.update(
            f"[bold #a78bfa]DIFF REVIEW[/]  {self.index + 1} / {n}\n"
            f"[bold]{path}[/]  ({action})  [green]+{add}[/] [red]-{rem}[/]\n"
            f"[dim]{self.status_note}[/]"
        )
        content.update(format_unified_diff_markup(diff_text))
        footer.update(
            "[dim]A accept · R reject · ← → navigate · Esc close[/]"
        )

    def action_prev(self) -> None:
        if self.paths:
            self.index = (self.index - 1) % len(self.paths)
            self.status_note = "Pending review"
            self._refresh()

    def action_next(self) -> None:
        if self.paths:
            self.index = (self.index + 1) % len(self.paths)
            self.status_note = "Pending review"
            self._refresh()

    def action_accept(self) -> None:
        path = self.current_path()
        if path:
            self.post_message(DiffAccept(path))

    def action_reject(self) -> None:
        path = self.current_path()
        if path:
            self.post_message(DiffReject(path))

    def action_close(self) -> None:
        self.post_message(DiffReviewClosed())

    @on(Button.Pressed, "#diff-accept")
    def on_accept_btn(self, event: Button.Pressed) -> None:
        event.stop()
        self.action_accept()

    @on(Button.Pressed, "#diff-reject")
    def on_reject_btn(self, event: Button.Pressed) -> None:
        event.stop()
        self.action_reject()

    @on(Button.Pressed, "#diff-prev")
    def on_prev_btn(self, event: Button.Pressed) -> None:
        event.stop()
        self.action_prev()

    @on(Button.Pressed, "#diff-next")
    def on_next_btn(self, event: Button.Pressed) -> None:
        event.stop()
        self.action_next()

    @on(Button.Pressed, "#diff-close")
    def on_close_btn(self, event: Button.Pressed) -> None:
        event.stop()
        self.action_close()

    def remove_path(self, path: str, note: str) -> None:
        if path in self.paths:
            i = self.paths.index(path)
            self.paths.pop(i)
            if self.index >= len(self.paths):
                self.index = max(0, len(self.paths) - 1)
        self.status_note = note
        self._refresh()
