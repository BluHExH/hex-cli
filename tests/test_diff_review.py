"""Diff review: tracker accept/reject and markup formatting."""
from __future__ import annotations

from pathlib import Path

from hex_cli.changes.tracker import ChangeTracker
from hex_cli.tui.widgets.diff_review import format_unified_diff_markup


def test_format_diff_colors_present():
    diff = "--- a/x\n+++ b/x\n@@ -1,2 +1,2 @@\n line\n-old\n+new\n"
    m = format_unified_diff_markup(diff)
    assert "[green]" in m
    assert "[red]" in m


def test_record_and_summary(tmp_path: Path):
    tr = ChangeTracker(tmp_path)
    f = tmp_path / "a.py"
    f.write_text("a=1\n", encoding="utf-8")
    tr.record("a.py", "modify", "a=1\n", "a=2\n")
    s = tr.summary()
    assert s["file_count"] == 1
    assert s["added"] >= 1
    assert "a.py" in tr.file_paths()
    d = tr.get_latest_for("a.py")
    assert d is not None
    assert "a=2" in (d.after or "")


def test_accept_drops_tracking(tmp_path: Path):
    tr = ChangeTracker(tmp_path)
    (tmp_path / "b.py").write_text("x", encoding="utf-8")
    tr.record("b.py", "modify", "x", "y")
    (tmp_path / "b.py").write_text("y", encoding="utf-8")
    r = tr.accept_file("b.py")
    assert r["ok"]
    assert "b.py" not in tr.file_paths()
    assert (tmp_path / "b.py").read_text(encoding="utf-8") == "y"


def test_reject_restores_original(tmp_path: Path):
    tr = ChangeTracker(tmp_path)
    (tmp_path / "c.py").write_text("orig\n", encoding="utf-8")
    tr.record("c.py", "modify", "orig\n", "new\n")
    (tmp_path / "c.py").write_text("new\n", encoding="utf-8")
    r = tr.reject_file("c.py")
    assert r["ok"]
    assert (tmp_path / "c.py").read_text(encoding="utf-8") == "orig\n"


def test_reject_refuses_external_edit(tmp_path: Path):
    tr = ChangeTracker(tmp_path)
    (tmp_path / "d.py").write_text("orig\n", encoding="utf-8")
    tr.record("d.py", "modify", "orig\n", "ai\n")
    (tmp_path / "d.py").write_text("user-changed\n", encoding="utf-8")
    r = tr.reject_file("d.py")
    assert r["ok"] is False
    assert "External" in r.get("error", "")
    assert (tmp_path / "d.py").read_text(encoding="utf-8") == "user-changed\n"


def test_unicode_and_windows_newlines(tmp_path: Path):
    tr = ChangeTracker(tmp_path)
    before = "হ্যালো\r\n"
    after = "হ্যালো\r\nবিশ্ব\r\n"
    tr.record("u.txt", "modify", before, after)
    rec = tr.get_latest_for("u.txt")
    assert rec is not None
    assert "হ্যালো" in rec.unified_diff()
    add, rem = rec.stats()
    assert add >= 1


def test_multiple_files_navigation_list(tmp_path: Path):
    tr = ChangeTracker(tmp_path)
    for name in ("a.py", "b.py", "c.py"):
        tr.record(name, "create", None, "content")
    paths = tr.file_paths()
    assert len(paths) == 3
