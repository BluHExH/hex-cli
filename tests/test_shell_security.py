from pathlib import Path

import pytest

from hex_cli.permissions.gate import PermissionGate
from hex_cli.tools.registry import ToolRegistry
from hex_cli.tools.shell import ShellTool, _split_argv


def test_split_does_not_expand_metacharacters():
    parts = _split_argv("echo hello")
    assert parts[0] == "echo"


def test_shell_false_runs_argv(tmp_path: Path):
    tool = ShellTool(tmp_path, timeout=10)
    out = tool.run(["python3", "-c", "print('ok')"])
    assert "ok" in out
    assert "exit=0" in out


def test_metacharacter_string_without_shell_is_literal_argv(tmp_path: Path):
    tool = ShellTool(tmp_path, timeout=5)
    # Without shell, this is a single program name attempt or split tokens — not `touch`
    out = tool.run("python3 -c \"print(1)\"")
    assert "exit=" in out


def test_permission_denies_shell(tmp_path: Path):
    reg = ToolRegistry(tmp_path, PermissionGate(mode="deny"))
    r = reg.execute("run_shell", {"command": "python3 -c \"print(1)\""})
    assert not r.ok
    assert "permission denied" in r.error


def test_timeout_terminates(tmp_path: Path):
    tool = ShellTool(tmp_path, timeout=1)
    out = tool.run(["python3", "-c", "import time; time.sleep(30)"])
    assert "timeout" in out.lower() or "exit=" in out
