"""Ensure hex_cli.context package exports required agent startup symbols."""
from pathlib import Path

from hex_cli.context import (
    discover_project_summary,
    load_key_file_snippets,
    inject_file_context,
    extract_mentions,
)


def test_discover_project_summary_runs(tmp_path: Path):
    (tmp_path / "README.md").write_text("# hello\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("x=1\n", encoding="utf-8")
    text = discover_project_summary(tmp_path)
    assert "Project root:" in text
    assert "README.md" in text or "Key files" in text


def test_load_key_file_snippets(tmp_path: Path):
    (tmp_path / "README.md").write_text("title\n" * 10, encoding="utf-8")
    s = load_key_file_snippets(tmp_path)
    assert "README.md" in s
    assert "title" in s


def test_agent_loop_imports_context():
    # Same import path used at TUI/agent startup
    from hex_cli.agent.loop import AgentLoop  # noqa: F401
    from hex_cli.context import discover_project_summary, load_key_file_snippets
    assert callable(discover_project_summary)
    assert callable(load_key_file_snippets)
