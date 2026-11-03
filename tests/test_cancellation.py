from pathlib import Path

from hex_cli.agent.runner import AgentRunner
from hex_cli.changes.tracker import ChangeLog
from hex_cli.config.settings import HexSettings
from hex_cli.permissions.gate import PermissionGate
from hex_cli.providers.base import ProviderResponse, ToolCall
from hex_cli.tools.registry import ToolRegistry


def test_cancel_stops_further_tool_rounds(tmp_path: Path):
    settings = HexSettings(workspace=str(tmp_path), permission_mode="allow", max_tool_rounds=8)
    tools = ToolRegistry(tmp_path, PermissionGate(mode="allow"))
    runner = AgentRunner(
        _CancelAfterFirstToolProvider(runner_holder := {}),
        tools,
        settings,
        ChangeLog(),
    )
    runner_holder["runner"] = runner
    result = runner.run_turn([], "go")
    assert result.cancelled is True
    assert result.assistant_text == "Cancelled."
    # only first tool should have run before cancel
    assert len(result.tool_events) >= 1


class _CancelAfterFirstToolProvider:
    name = "cancel_prov"
    model = "c"

    def __init__(self, holder: dict) -> None:
        self.holder = holder
        self.calls = 0

    def complete(self, messages, tools=None):
        self.calls += 1
        if self.calls == 1:
            return ProviderResponse(
                content="",
                tool_calls=[ToolCall(id="1", name="list_dir", arguments={"path": "."})],
            )
        # Second model call: cancel before returning
        self.holder["runner"].request_cancel()
        return ProviderResponse(
            content="",
            tool_calls=[ToolCall(id="2", name="list_dir", arguments={"path": "."})],
        )

    def stream_text(self, messages):
        yield ""


def test_request_cancel_api(tmp_path: Path):
    settings = HexSettings(workspace=str(tmp_path), permission_mode="allow")
    tools = ToolRegistry(tmp_path, PermissionGate(mode="allow"))
    runner = AgentRunner(
        type("P", (), {"name": "p", "model": "m", "complete": lambda *a, **k: ProviderResponse(content="ok"), "stream_text": lambda *a, **k: iter(())})(),
        tools,
        settings,
        ChangeLog(),
    )
    runner.request_cancel()
    assert runner._cancel.is_set()
