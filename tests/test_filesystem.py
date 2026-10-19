"""Tests for filesystem tools."""

from __future__ import annotations

from pathlib import Path

import pytest

from hex_cli.config import AppConfig, PermissionConfig
from hex_cli.permissions import PermissionManager
from hex_cli.tools.filesystem import FileSystemTools


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("def hello():\n    return 42\n")
    (tmp_path / "README.md").write_text("# Demo\n")
    return tmp_path


@pytest.fixture
def fs(project: Path) -> FileSystemTools:
    cfg = AppConfig(permissions=PermissionConfig(
        read_files="allow",
        create_files="allow",
        modify_files="allow",
    ))
    pm = PermissionManager(cfg, project, ask_fn=lambda r: True)
    return FileSystemTools(project, pm, cfg)


def test_list_files(fs: FileSystemTools):
    result = fs.list_files(".")
    assert result["ok"]
    entries = result["entries"]
    assert any("README.md" in e for e in entries)
    assert any("src" in e for e in entries)


def test_read_file(fs: FileSystemTools):
    result = fs.read_file("src/app.py")
    assert result["ok"]
    assert "hello" in result["content"]
    assert result["total_lines"] == 2


def test_read_file_missing(fs: FileSystemTools):
    result = fs.read_file("nope.py")
    assert result["ok"] is False


def test_read_file_traversal(fs: FileSystemTools):
    result = fs.read_file("../secret")
    assert result["ok"] is False
    assert "escape" in result["error"].lower() or "project root" in result["error"].lower()


def test_write_and_edit(fs: FileSystemTools, project: Path):
    r = fs.write_file("src/new.py", "x = 1\n")
    assert r["ok"]
    assert (project / "src" / "new.py").read_text() == "x = 1\n"

    r2 = fs.edit_file("src/new.py", "x = 1", "x = 2")
    assert r2["ok"]
    assert (project / "src" / "new.py").read_text() == "x = 2\n"
    assert (project / "src" / "new.py.hexbak").exists()


def test_edit_not_found_string(fs: FileSystemTools):
    r = fs.edit_file("src/app.py", "DOES_NOT_EXIST", "x")
    assert r["ok"] is False


def test_search_text(fs: FileSystemTools):
    r = fs.search_text("hello")
    assert r["ok"]
    assert r["count"] >= 1
    assert any(m["file"].endswith("app.py") for m in r["matches"])


def test_create_directory(fs: FileSystemTools, project: Path):
    r = fs.create_directory("src/utils")
    assert r["ok"]
    assert (project / "src" / "utils").is_dir()


def test_write_rejected_when_ask_denied(project: Path):
    cfg = AppConfig(permissions=PermissionConfig(create_files="ask"))
    pm = PermissionManager(cfg, project, ask_fn=lambda r: False)
    fs = FileSystemTools(project, pm, cfg)
    r = fs.write_file("evil.py", "pass")
    assert r["ok"] is False
    assert r.get("skipped") is True
    assert not (project / "evil.py").exists()
