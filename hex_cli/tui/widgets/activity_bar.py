"""Real activity indicator driven by agent state (not decorative fake progress)."""

from __future__ import annotations

from textual.reactive import reactive
from textual.widgets import Static

_SPINNER = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")

# Map tool names / phases to human labels — only shown when that activity occurs
PHASE_LABELS = {
    "idle": "",
    "thinking": "Thinking",
    "planning": "Planning",
    "read_file": "Reading files",
    "list_directory": "Listing directory",
    "search_files": "Searching project",
    "grep": "Searching project",
    "write_file": "Writing changes",
    "edit_file": "Writing changes",
    "apply_patch": "Applying patch",
    "run_command": "Executing command",
    "run_tests": "Running tests",
    "git_status": "Checking git",
    "git_diff": "Reviewing changes",
    "git_commit": "Committing",
    "completed": "Completed",
    "cancelled": "Cancelled",
    "error": "Error",
}


class ActivityBar(Static):
    """Docked activity line with spinner while agent is busy."""

    phase: reactive[str] = reactive("idle")
    busy: reactive[bool] = reactive(False)
    detail: reactive[str] = reactive("")

    def __init__(self, **kwargs) -> None:
        super().__init__(id="activity-bar", **kwargs)
        self._spin_i = 0
        self._timer = None

    def on_mount(self) -> None:
        self._timer = self.set_interval(0.12, self._tick)
        self._render()

    def on_unmount(self) -> None:
        if self._timer is not None:
            try:
                self._timer.stop()
            except Exception:
                pass

    def _tick(self) -> None:
        if self.busy:
            self._spin_i = (self._spin_i + 1) % len(_SPINNER)
            self._render()

    def watch_phase(self, _value: str) -> None:
        self._render()

    def watch_busy(self, value: bool) -> None:
        if not value:
            self._spin_i = 0
        self._render()

    def watch_detail(self, _value: str) -> None:
        self._render()

    def set_activity(self, phase: str, *, busy: bool | None = None, detail: str = "") -> None:
        self.phase = phase
        if busy is not None:
            self.busy = busy
        if detail:
            self.detail = detail[:80]
        elif not busy:
            self.detail = ""

    def _render(self) -> None:
        if not self.busy and self.phase in ("idle", "completed", ""):
            self.update("")
            self.display = False
            return
        self.display = True
        label = PHASE_LABELS.get(self.phase, self.phase.replace("_", " ").title())
        if self.busy:
            spin = _SPINNER[self._spin_i]
            extra = f"  {self.detail}" if self.detail else ""
            self.update(f"[bold #d29922]{spin} {label}…[/]{extra}")
        else:
            self.update(f"[dim]{label}[/]")
