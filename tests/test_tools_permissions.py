from pathlib import Path

from hex_cli.permissions.gate import PermissionGate, PermissionRequest
from hex_cli.tools.registry import ToolRegistry


def test_path_jail(tmp_path: Path):
    gate = PermissionGate(mode="allow")
    tools = ToolRegistry(tmp_path, gate)
    (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
    r = tools.execute("read_file", {"path": "a.txt"})
    assert r.ok and "hello" in r.output
    r2 = tools.execute("read_file", {"path": "../outside"})
    assert not r2.ok


def test_write_and_list(tmp_path: Path):
    tools = ToolRegistry(tmp_path, PermissionGate(mode="allow"))
    assert tools.execute("write_file", {"path": "x.py", "content": "print(1)\n"}).ok
    listed = tools.execute("list_dir", {"path": "."})
    assert listed.ok and "x.py" in listed.output


def test_permission_deny_shell(tmp_path: Path):
    tools = ToolRegistry(tmp_path, PermissionGate(mode="deny"))
    r = tools.execute("run_shell", {"command": "echo hi"})
    assert not r.ok and "permission denied" in r.error
