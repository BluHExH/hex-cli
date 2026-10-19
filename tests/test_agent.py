"""Tests for agent tool dispatch and validation (no live network)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from hex_cli.agent.loop import AgentLoop
from hex_cli.config import AppConfig, PermissionConfig
from hex_cli.permissions import PermissionManager
from hex_cli.providers.base import BaseProvider, ChatMessage, ProviderResponse, ToolCall


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "hello.py").write_text("print('hello')\n")
    return tmp_path


@pytest.fixture
def agent(project: Path) -> AgentLoop:
    cfg = AppConfig(
        permissions=PermissionConfig(
            read_files="allow",
            create_files="allow",
            modify_files="allow",
            run_commands="deny",
        ),
        max_agent_steps=5,
    )
    pm = PermissionManager(cfg, project, ask_fn=lambda r: True)
    provider = MagicMock(spec=BaseProvider)
    provider.model = "test-model"
    return AgentLoop(project, provider, cfg, pm)


def test_dispatch_list_files(agent: AgentLoop):
    tc = ToolCall(id="1", name="list_files", arguments={"path": "."})
    result = agent._dispatch_tool(tc)
    assert result["ok"] is True
    assert result["count"] >= 1


def test_dispatch_read_file(agent: AgentLoop):
    tc = ToolCall(id="2", name="read_file", arguments={"path": "hello.py"})
    result = agent._dispatch_tool(tc)
    assert result["ok"] is True
    assert "hello" in result["content"]


def test_dispatch_missing_path(agent: AgentLoop):
    tc = ToolCall(id="3", name="read_file", arguments={})
    result = agent._dispatch_tool(tc)
    assert result["ok"] is False
    assert "path" in result["error"].lower()


def test_dispatch_unknown_tool(agent: AgentLoop):
    tc = ToolCall(id="4", name="execute_python", arguments={"code": "1+1"})
    result = agent._dispatch_tool(tc)
    assert result["ok"] is False
    assert "unknown" in result["error"].lower()


def test_dispatch_invalid_json_args(agent: AgentLoop):
    tc = ToolCall(id="5", name="read_file", arguments={"_raw": "not-json{"})
    result = agent._dispatch_tool(tc)
    assert result["ok"] is False


def test_dispatch_write_file(agent: AgentLoop, project: Path):
    tc = ToolCall(
        id="6",
        name="write_file",
        arguments={"path": "new.txt", "content": "data\n"},
    )
    result = agent._dispatch_tool(tc)
    assert result["ok"] is True
    assert (project / "new.txt").read_text() == "data\n"


def test_dispatch_run_command_denied(agent: AgentLoop):
    tc = ToolCall(id="7", name="run_command", arguments={"command": "echo hi"})
    result = agent._dispatch_tool(tc)
    assert result["ok"] is False


def test_agent_run_no_tools(agent: AgentLoop):
    agent.provider.chat.return_value = ProviderResponse(
        content="The file looks fine.",
        tool_calls=[],
    )
    text = agent.run("Check hello.py")
    assert "fine" in text
    assert agent.provider.chat.call_count == 1


def test_agent_run_with_tool(agent: AgentLoop):
    agent.provider.chat.side_effect = [
        ProviderResponse(
            content="Let me list files.",
            tool_calls=[ToolCall(id="t1", name="list_files", arguments={"path": "."})],
        ),
        ProviderResponse(content="Done listing.", tool_calls=[]),
    ]
    text = agent.run("List the project")
    assert "Done" in text
    assert agent.provider.chat.call_count == 2
