"""Stage 5: subagents, MCP, skills, commands, LSP, worktrees."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from hex_cli.commands_ext.loader import CommandLoader, RESERVED
from hex_cli.mcp.client import MCPClient, MCPServerConfig, MCPTool
from hex_cli.skills.loader import SkillLoader, Skill
from hex_cli.subagents.runtime import DelegationLimits, SubagentRuntime, SubagentResult
from hex_cli.tui.widgets.tool_card import ToolCard, ToolCardState
from hex_cli.worktree.manager import WorktreeManager


# ---------------------------------------------------------------------------
# Subagents
# ---------------------------------------------------------------------------

def test_delegation_limits():
    limits = DelegationLimits(max_depth=2, max_concurrent=3)
    assert limits.max_depth == 2
    assert limits.max_concurrent == 3


def test_subagent_result_merge():
    from hex_cli.subagents.runtime import SubagentRuntime
    # merge_results is instance method — use a lightweight stub
    class _Stub:
        def merge_results(self, results):
            return SubagentRuntime.merge_results(self, results)

    results = [
        SubagentResult(task_id="a", agent="explore", ok=True, summary="found X", duration_ms=10),
        SubagentResult(task_id="b", agent="plan", ok=False, summary="fail", error="boom", duration_ms=5),
    ]
    text = _Stub().merge_results(results)
    assert "Subagent results" in text
    assert "explore" in text
    assert "error" in text


def test_subagent_depth_guard(tmp_path):
    from hex_cli.config import AppConfig
    from hex_cli.permissions import PermissionManager

    cfg = AppConfig()
    perms = PermissionManager(cfg, tmp_path)

    def fake_provider():
        raise RuntimeError("no provider in unit test")

    rt = SubagentRuntime(tmp_path, cfg, perms, fake_provider, limits=DelegationLimits(max_depth=1))
    res = rt.run_one("test", "explore", depth=5)
    assert res.ok is False
    assert "depth" in (res.error or "").lower() or "depth" in res.summary.lower()


# ---------------------------------------------------------------------------
# MCP
# ---------------------------------------------------------------------------

def test_mcp_client_list_empty():
    client = MCPClient()
    assert client.list_servers() == []
    assert client.list_tools() == []


def test_mcp_http_rejected():
    client = MCPClient()
    result = client.connect(
        MCPServerConfig(name="x", command=[], transport="http", url="http://localhost")
    )
    assert result["ok"] is False
    assert "HTTP" in result["error"]


def test_mcp_tool_namespace():
    t = MCPTool(server="fs", name="read", description="r", input_schema={"type": "object"})
    assert t.namespaced_name == "mcp__fs__read"


def test_mcp_openai_schemas():
    client = MCPClient()
    # Inject a fake session tool list
    class FakeSession:
        tools = [
            MCPTool(server="demo", name="ping", description="ping", input_schema={"type": "object"})
        ]
        connected = True
        config = type("C", (), {"transport": "stdio"})()
        last_error = None

    client._sessions["demo"] = FakeSession()  # type: ignore
    schemas = client.openai_tool_schemas()
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "mcp__demo__ping"


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

def test_skill_loader_discovery(tmp_path):
    skill_dir = tmp_path / ".hex" / "skills" / "review-security"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: review-security\ndescription: Security review\nagents: [build, plan]\n---\n"
        "Look for injection and secret leaks.\n",
        encoding="utf-8",
    )
    loader = SkillLoader(tmp_path)
    n = loader.reload()
    assert n == 1
    s = loader.get("review-security")
    assert s is not None
    assert s.applies_to("build")
    assert not s.applies_to("explore")
    assert "injection" in s.instructions


def test_skill_invalid_name_skipped(tmp_path):
    bad = tmp_path / ".hex" / "skills" / "bad name"
    bad.mkdir(parents=True)
    (bad / "SKILL.md").write_text("---\nname: bad name\n---\nbody\n", encoding="utf-8")
    loader = SkillLoader(tmp_path)
    loader.reload()
    # name with space fails validation
    assert loader.get("bad name") is None


# ---------------------------------------------------------------------------
# Custom commands
# ---------------------------------------------------------------------------

def test_custom_command_render(tmp_path):
    cmd_dir = tmp_path / ".hex" / "commands"
    cmd_dir.mkdir(parents=True)
    (cmd_dir / "fix-tests.md").write_text(
        "---\ndescription: Fix failing tests\nagent: build\n---\n"
        "Fix the failing tests: {{args}}\nFocus on {{arg1}}.\n",
        encoding="utf-8",
    )
    loader = CommandLoader(tmp_path)
    assert loader.reload() == 1
    cmd = loader.get("fix-tests")
    assert cmd is not None
    rendered = cmd.render("auth module")
    assert "auth module" in rendered
    assert "auth" in rendered


def test_reserved_commands_not_overridden(tmp_path):
    cmd_dir = tmp_path / ".hex" / "commands"
    cmd_dir.mkdir(parents=True)
    (cmd_dir / "help.md").write_text("---\ndescription: x\n---\nShould not load\n", encoding="utf-8")
    loader = CommandLoader(tmp_path)
    loader.reload()
    assert loader.get("help") is None
    assert "help" in RESERVED


# ---------------------------------------------------------------------------
# Tool cards
# ---------------------------------------------------------------------------

def test_tool_card_states():
    card = ToolCard("run_command", risk="medium", args_summary="pytest -q")
    assert card.state == ToolCardState.RUNNING
    card.set_state(ToolCardState.COMPLETED, output="5 passed")
    assert card.state == ToolCardState.COMPLETED
    assert card.duration_ms >= 0
    text = card.as_text()
    assert "run_command" in text
    assert "completed" in text


def test_tool_card_denied():
    card = ToolCard("write_file", risk="medium")
    card.set_state(ToolCardState.DENIED, error="user denied")
    assert "denied" in card.as_text()


# ---------------------------------------------------------------------------
# Worktrees (graceful without repo)
# ---------------------------------------------------------------------------

def test_worktree_not_a_repo(tmp_path):
    wt = WorktreeManager(tmp_path)
    result = wt.list_worktrees()
    assert result["ok"] is False


def test_worktree_list_on_hex_repo():
    root = Path(__file__).resolve().parents[1]
    wt = WorktreeManager(root)
    result = wt.list_worktrees()
    # hex-cli itself is a git repo in the sandbox
    if result.get("ok"):
        assert "worktrees" in result
        assert isinstance(result["worktrees"], list)


# ---------------------------------------------------------------------------
# Project config merge
# ---------------------------------------------------------------------------

def test_project_config_cannot_loosen_permissions(tmp_path):
    from hex_cli.config import AppConfig, ProjectConfig, merge_project_config, PermissionConfig

    app = AppConfig(permissions=PermissionConfig(run_commands="deny", modify_files="ask"))
    proj = ProjectConfig(permissions=PermissionConfig(run_commands="allow", modify_files="allow"))
    merged = merge_project_config(app, proj)
    # deny stays deny; ask stays ask (cannot loosen to allow)
    assert merged.permissions.run_commands == "deny"
    assert merged.permissions.modify_files == "ask"


def test_project_config_can_tighten(tmp_path):
    from hex_cli.config import AppConfig, ProjectConfig, merge_project_config, PermissionConfig

    app = AppConfig(permissions=PermissionConfig(run_commands="allow"))
    proj = ProjectConfig(permissions=PermissionConfig(run_commands="ask"))
    merged = merge_project_config(app, proj)
    assert merged.permissions.run_commands == "ask"
