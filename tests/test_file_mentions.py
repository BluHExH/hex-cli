"""@ mention parsing, security, and context injection."""
from __future__ import annotations

from pathlib import Path

from hex_cli.context.file_mentions import (
    extract_mentions,
    inject_file_context,
    resolve_mention,
)
from hex_cli.tui.file_index import search_files, list_project_files


def test_extract_mentions_multiple():
    text = "See @src/main.py and @src/config.py please"
    m = extract_mentions(text)
    assert "src/main.py" in m
    assert "src/config.py" in m


def test_resolve_and_inject(tmp_path: Path):
    (tmp_path / "src").mkdir()
    f = tmp_path / "src" / "main.py"
    f.write_text("print('hello')\n", encoding="utf-8")
    aug, meta = inject_file_context("Explain @src/main.py", tmp_path)
    assert "print('hello')" in aug
    assert meta and meta[0]["ok"]
    assert "Attached file context" in aug or "File: src/main.py" in aug


def test_path_traversal_blocked(tmp_path: Path):
    outside = tmp_path.parent / "secret.txt"
    outside.write_text("secret", encoding="utf-8")
    r = resolve_mention(tmp_path, "../secret.txt")
    assert r is None
    aug, meta = inject_file_context("x @../secret.txt", tmp_path)
    assert "secret" not in aug or meta[0]["ok"] is False


def test_sensitive_env_blocked(tmp_path: Path):
    (tmp_path / ".env").write_text("API_KEY=secret\n", encoding="utf-8")
    # list_project_files may skip dotfiles; force inject path
    aug, meta = inject_file_context("leak @.env", tmp_path)
    assert "API_KEY=secret" not in aug
    assert any(not m.get("ok") for m in meta) or ".env" in aug


def test_search_files_ranks(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x", encoding="utf-8")
    (tmp_path / "src" / "manager.py").write_text("y", encoding="utf-8")
    results = search_files(tmp_path, "main", limit=10)
    assert results
    assert any("main" in r for r in results)


def test_duplicate_mentions_deduped():
    m = extract_mentions("@a.py @a.py @b.py")
    assert m.count("a.py") == 1
    assert "b.py" in m
