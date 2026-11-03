from __future__ import annotations

import os
import signal
import subprocess
import threading
from pathlib import Path
from typing import Sequence


class ShellTool:
    """Workspace-bound command runner.

    Default path uses argv list + shell=False (no shell metacharacter expansion).
    Explicit shell mode is opt-in and still requires the permission gate.
    """

    def __init__(self, root: Path, timeout: float = 60.0) -> None:
        self.root = root.resolve()
        self.timeout = timeout
        self._proc: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()

    def run(self, command: str | Sequence[str], *, use_shell: bool = False) -> str:
        if isinstance(command, str):
            if use_shell:
                argv: str | list[str] = command
                shell = True
            else:
                argv = _split_argv(command)
                shell = False
        else:
            argv = list(command)
            shell = False

        with self._lock:
            self._proc = subprocess.Popen(
                argv,
                shell=shell,
                cwd=str(self.root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
            )
            proc = self._proc
        try:
            out, _ = proc.communicate(timeout=self.timeout)
        except subprocess.TimeoutExpired:
            self.cancel()
            out, _ = proc.communicate(timeout=5)
            out = (out or "") + "\n[timeout — process terminated]"
        finally:
            with self._lock:
                if self._proc is proc:
                    self._proc = None
        return f"exit={proc.returncode}\n{(out or '')[:20_000]}"

    def cancel(self) -> None:
        with self._lock:
            proc = self._proc
        if proc is None or proc.poll() is not None:
            return
        try:
            if os.name == "nt":
                proc.terminate()
            else:
                os.killpg(proc.pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError, OSError):
            try:
                proc.kill()
            except OSError:
                pass


def _split_argv(command: str) -> list[str]:
    """POSIX-like split without executing a shell.

    On Windows, uses a conservative split that still avoids cmd metacharacters
    by not invoking COMSPEC.
    """
    try:
        import shlex

        return shlex.split(command, posix=os.name != "nt")
    except ValueError as exc:
        raise ValueError(f"invalid command string: {exc}") from exc
