"""Stage 3: tool registry, project tools, change tracker, agent dispatch."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from hex_cli.changes.tracker import ChangeTracker
from hex_cli.config import AppConfig
from hex_cli.permissions import PermissionManager
from hex_cli.providers.base import ToolCall
from hex_cli.tools.project import ProjectTools
from hex_cli.tools.registry import get_tool_spec, list_tools_for_display, openai_tool_schemas, tool_names


def test_tool_registry_has_core_tools() -> None:
    names = set(tool_names())
    for required in (
        "read_file", "write_file", "edit_file", "list_files", "search_text",
        "glob", "run_command", "project_overview", "detect_project_type", "apply_patch",
    ):
        assert required in names
    schemas = openai_tool_schemas()
    assert len(schemas) == len(names)
    assert get_tool_spec("read_file") is not None
    assert get_tool_spec("nope") is None


def test_project_detect_and_overview(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print(1)\n", encoding="utf-8")
    cfg = AppConfig()
    pm = PermissionManager(cfg, tmp_path)
    tools = ProjectTools(tmp_path, pm, cfg)
    det = tools.detect_project_type()
    assert det["ok"] and "python" in det["types"]
    ov = tools.project_overview()
    assert ov["ok"]
    g = tools.glob("**/*.py")
    assert g["ok"] and any(m.endswith("main.py") for m in g["matches"])


def test_change_tracker_diff_and_undo(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_text("hello\n", encoding="utf-8")
    tracker = ChangeTracker(tmp_path)
    tracker.record("a.txt", "modify", "hello\n", "hello\nworld\n")
    s = tracker.summary()
    assert s["file_count"] == 1
    f.write_text("hello\nworld\n", encoding="utf-8")
    result = tracker.undo_last()
    assert result["ok"]
    assert f.read_text(encoding="utf-8") == "hello\n"


def test_path_traversal_denied(tmp_path: Path) -> None:
    from hex_cli.tools.filesystem import FileSystemTools
    cfg = AppConfig()
    pm = PermissionManager(cfg, tmp_path)
    fs = FileSystemTools(tmp_path, pm, cfg)
    r = fs.read_file(path="../../etc/passwd")
    assert r["ok"] is False
