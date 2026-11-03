from __future__ import annotations

import subprocess
from pathlib import Path


class ShellTool:
    def __init__(self, root: Path, timeout: float = 60.0) -> None:
        self.root = root.resolve()
        self.timeout = timeout

    def run(self, command: str) -> str:
        # No shell=True injection of secrets; still dangerous — permission gate required.
        proc = subprocess.run(
            command,
            shell=True,
            cwd=str(self.root),
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return f"exit={proc.returncode}\n{out[:20_000]}"
