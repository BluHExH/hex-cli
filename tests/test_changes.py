from pathlib import Path

from hex_cli.changes.tracker import ChangeLog


def test_restore(tmp_path: Path):
    p = tmp_path / "a.txt"
    p.write_text("old", encoding="utf-8")
    log = ChangeLog()
    log.record_write("a.txt", "old", "new")
    p.write_text("new", encoding="utf-8")
    restored = log.restore_last(tmp_path)
    assert restored is not None
    assert p.read_text(encoding="utf-8") == "old"
