"""Shell command execution with approval and limits."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from hex_cli.config import AppConfig
from hex_cli.permissions import ActionType, PermissionManager


class CommandTools:
    def __init__(
        self,
        project_root: Path,
        permissions: PermissionManager,
        config: AppConfig,
    ):
        self.root = project_root.resolve()
        self.perms = permissions
        self.config = config

    def run_command(
        self,
        command: str,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        if not command or not command.strip():
            return {"ok": False, "error": "Empty command"}

        timeout = timeout or self.config.command_timeout_seconds
        high = self.perms.is_high_impact_command(command)

        result = self.perms.check(
            ActionType.RUN_COMMAND,
            f"Run command: {command}",
            detail=command,
            force_ask=high,
        )
        if not result.allowed:
            return {"ok": False, "error": result.reason, "skipped": True}

        # Use shell=True for convenience on Windows/Unix; isolation is limited.
        # Documented limitation: command blocklist is not a full sandbox.
        env = os.environ.copy()
        # Avoid inheriting interactive prompts
        env.setdefault("PYTHONUNBUFFERED", "1")
        env.setdefault("CI", "1")

        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=str(self.root),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "error": f"Command timed out after {timeout}s",
                "command": command,
            }
        except OSError as e:
            return {"ok": False, "error": str(e), "command": command}

        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        max_chars = self.config.max_command_output_chars
        truncated = False
        if len(stdout) > max_chars:
            stdout = stdout[:max_chars] + "\n… (stdout truncated)"
            truncated = True
        if len(stderr) > max_chars:
            stderr = stderr[:max_chars] + "\n… (stderr truncated)"
            truncated = True

        return {
            "ok": proc.returncode == 0,
            "command": command,
            "exit_code": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "truncated": truncated,
        }

    def run_tests(self, args: str = "") -> dict[str, Any]:
        """Run pytest if available, otherwise try common alternatives."""
        # Prefer pytest
        cmd = f"{sys.executable} -m pytest {args}".strip()
        # Quick check that pytest is importable
        check = subprocess.run(
            [sys.executable, "-c", "import pytest"],
            capture_output=True,
            cwd=str(self.root),
        )
        if check.returncode != 0:
            # Fallbacks
            if (self.root / "package.json").exists():
                cmd = f"npm test {args}".strip()
            elif (self.root / "Cargo.toml").exists():
                cmd = f"cargo test {args}".strip()
            else:
                return {
                    "ok": False,
                    "error": "No test runner detected (pytest / npm test / cargo test)",
                }

        return self.run_command(cmd, timeout=self.config.command_timeout_seconds * 2)
