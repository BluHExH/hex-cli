from pathlib import Path

from hex_cli.agent.runner import AgentRunner
from hex_cli.changes.tracker import ChangeLog
from hex_cli.config.settings import HexSettings
from hex_cli.permissions.gate import PermissionGate
from hex_cli.providers.mock import MockProvider
from hex_cli.tools.registry import ToolRegistry


def test_mock_read_tool(tmp_path: Path):
    (tmp_path / "f.txt").write_text("data", encoding="utf-8")
    settings = HexSettings(workspace=str(tmp_path), provider="mock", permission_mode="allow")
    tools = ToolRegistry(tmp_path, PermissionGate(mode="allow"))
    runner = AgentRunner(MockProvider(), tools, settings, ChangeLog())
    result = runner.run_turn([], "READ f.txt")
    assert result.tool_events and result.tool_events[0]["ok"]
    assert "data" in result.assistant_text


def test_mock_write_tracked(tmp_path: Path):
    settings = HexSettings(workspace=str(tmp_path), provider="mock", permission_mode="allow")
    changes = ChangeLog()
    tools = ToolRegistry(tmp_path, PermissionGate(mode="allow"))
    runner = AgentRunner(MockProvider(), tools, settings, changes)
    result = runner.run_turn([], "WRITE note.txt :: hello world")
    assert (tmp_path / "note.txt").read_text(encoding="utf-8") == "hello world"
    assert changes.items
