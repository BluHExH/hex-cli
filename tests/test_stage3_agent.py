"""Stage 3: tool registry, project tools, change tracker, agent dispatch."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from hex_cli.changes.tracker import ChangeTracker
from hex_cli.config import AppConfig
from hex_cli.permissions import PermissionManager
from hex_cli.providers.base import ToolCall
from hex_cli.tools.project import ProjectTools
from hex_cli.tools.registry import (
    get_tool_spec,
    list_tools_for_display,
    openai_tool_schemas,
    tool_names,
)


def test_tool_registry_has_core_tools() -> None:
    names = set(tool_names())
    for required in (
        "read_file",
        "write_file",
        "edit_file",
        "list_files",
        "search_text",
        "glob",
        "run_command",
        "project_overview",
        "detect_project_type",
        "apply_patch",
    ):
        assert required in names
    schemas = openai_tool_schemas()
    assert len(schemas) == len(names)
    assert all(s["type"] == "function" for s in schemas)
    assert get_tool_spec("read_file") is not None
    assert get_tool_spec("nope") is None
    display = list_tools_for_display()
    assert all("risk" in d for d in display)


def test_project_detect_and_overview(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print(1)\n", encoding="utf-8")
    cfg = AppConfig()
    pm = PermissionManager(cfg, tmp_path)
    tools = ProjectTools(tmp_path, pm, cfg)
    det = tools.detect_project_type()
    assert det["ok"]
    assert "python" in det["types"]
    ov = tools.project_overview()
    assert ov["ok"]
    assert ov["root"] == str(tmp_path.resolve())
    g = tools.glob("**/*.py")
    assert g["ok"]
    assert any(m.endswith("main.py") for m in g["matches"])


def test_change_tracker_diff_and_undo(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_text("hello\n", encoding="utf-8")
    tracker = ChangeTracker(tmp_path)
    tracker.record("a.txt", "modify", "hello\n", "hello\nworld\n")
    s = tracker.summary()
    assert s["file_count"] == 1
    assert s["added"] >= 1
    diff = tracker.all_diffs()
    assert "a.txt" in diff or "+world" in diff
    # apply change then undo
    f.write_text("hello\nworld\n", encoding="utf-8")
    result = tracker.undo_last()
    assert result["ok"]
    assert f.read_text(encoding="utf-8") == "hello\n"


def test_filesystem_glob(tmp_path: Path) -> None:
    from hex_cli.tools.filesystem import FileSystemTools

    (tmp_path / "x.py").write_text("x", encoding="utf-8")
    (tmp_path / "y.txt").write_text("y", encoding="utf-8")
    cfg = AppConfig()
    pm = PermissionManager(cfg, tmp_path)
    # allow all for tests
    pm.set_ask_callback(lambda req: True)
    fs = FileSystemTools(tmp_path, pm, cfg)
    r = fs.glob("*.py")
    assert r["ok"]
    assert "x.py" in r["matches"]


def test_agent_dispatch_read(tmp_path: Path) -> None:
    from hex_cli.agent.loop import AgentLoop
    from hex_cli.providers.base import BaseProvider

    (tmp_path / "hello.txt").write_text("hi there\n", encoding="utf-8")
    cfg = AppConfig()
    pm = PermissionManager(cfg, tmp_path)
    pm.set_ask_callback(lambda req: True)
    provider = MagicMock(spec=BaseProvider)
    agent = AgentLoop(tmp_path, provider, cfg, pm)
    result = agent._dispatch_tool(
        ToolCall(id="1", name="read_file", arguments={"path": "hello.txt"})
    )
    assert result["ok"]
    assert "hi there" in result.get("content", "") or "hi there" in str(result)


def test_agent_plan_mode_blocks_write(tmp_path: Path) -> None:
    from hex_cli.agent.loop import AgentLoop
    from hex_cli.providers.base import BaseProvider, ProviderResponse

    cfg = AppConfig()
    pm = PermissionManager(cfg, tmp_path)
    pm.set_ask_callback(lambda req: True)
    provider = MagicMock(spec=BaseProvider)
    # First response: try to write; second: done
    provider.chat.side_effect = [
        ProviderResponse(
            content="I will write",
            tool_calls=[
                ToolCall(
                    id="t1",
                    name="write_file",
                    arguments={"path": "evil.py", "content": "x"},
                )
            ],
        ),
        ProviderResponse(content="Plan only.", tool_calls=[]),
    ]
    agent = AgentLoop(tmp_path, provider, cfg, pm)
    agent.run("add a file", plan_only=True)
    assert not (tmp_path / "evil.py").exists()


def test_path_traversal_denied(tmp_path: Path) -> None:
    from hex_cli.tools.filesystem import FileSystemTools

    cfg = AppConfig()
    pm = PermissionManager(cfg, tmp_path)
    fs = FileSystemTools(tmp_path, pm, cfg)
    r = fs.read_file(path="../../etc/passwd")
    assert r["ok"] is False
