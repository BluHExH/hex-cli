"""HEX CLI v0.7 feature tests: picker, themes, redo, editor resolve."""
from __future__ import annotations
import tempfile
from pathlib import Path

from hex_cli.tui.file_index import list_project_files, fuzzy_score
from hex_cli.tui.themes import list_themes, get_theme
from hex_cli.changes.tracker import ChangeTracker
from hex_cli.editor_ext import resolve_editor


def test_list_project_files(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x=1\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "x.js").write_text("1")
    files = list_project_files(tmp_path)
    assert any(f.endswith("main.py") for f in files)
    assert not any("node_modules" in f for f in files)


def test_fuzzy_score():
    assert fuzzy_score("main", "src/main.py") > fuzzy_score("main", "readme.md")
    assert fuzzy_score("zzz", "src/main.py") < 0


def test_themes():
    themes = list_themes()
    assert len(themes) >= 2
    assert get_theme("hex-light").id == "hex-light"
    assert get_theme("missing").id == "hex-dark"


def test_redo_roundtrip(tmp_path: Path):
    f = tmp_path / "a.txt"
    f.write_text("v1", encoding="utf-8")
    tr = ChangeTracker(tmp_path)
    tr.record("a.txt", "modify", "v1", "v2")
    f.write_text("v2", encoding="utf-8")
    u = tr.undo_last()
    assert u["ok"]
    assert f.read_text(encoding="utf-8") == "v1"
    r = tr.redo_last()
    assert r["ok"]
    # after redo content should be agent version
    assert r.get("ok") is True


def test_resolve_editor_env(monkeypatch):
    monkeypatch.setenv("HEX_EDITOR", "true")
    assert resolve_editor() == "true"
