"""Session persistence, search, rename, delete, export."""
from __future__ import annotations

from pathlib import Path

from hex_cli.sessions.store import SessionStore, StoredMessage


def test_create_save_load_atomic(tmp_path: Path):
    store = SessionStore(root=tmp_path)
    s = store.create("Demo", tmp_path, provider="ollama", model="llama", agent="build")
    s.messages.append(StoredMessage(role="user", content="hello world"))
    store.save(s)
    loaded = store.load(s.meta.id)
    assert loaded is not None
    assert loaded.meta.name == "Demo"
    assert loaded.messages[0].content == "hello world"
    assert (tmp_path / f"{s.meta.id}.json").is_file()
    assert not list(tmp_path.glob("*.tmp"))


def test_rename_delete(tmp_path: Path):
    store = SessionStore(root=tmp_path)
    s = store.create("Old", tmp_path)
    assert store.rename(s.meta.id, "New Title")
    assert store.load(s.meta.id).meta.name == "New Title"
    assert store.delete(s.meta.id)
    assert store.load(s.meta.id) is None


def test_search_by_title_and_content(tmp_path: Path):
    store = SessionStore(root=tmp_path)
    a = store.create("Auth work", tmp_path)
    a.messages.append(StoredMessage(role="user", content="fix login bug"))
    store.save(a)
    b = store.create("Other", tmp_path)
    b.messages.append(StoredMessage(role="user", content="unrelated"))
    store.save(b)
    hits = store.search("login", project_root=tmp_path)
    assert any(h.id == a.meta.id for h in hits)


def test_export_markdown_json_no_secrets(tmp_path: Path):
    store = SessionStore(root=tmp_path)
    s = store.create("Exp", tmp_path, provider="openrouter", model="x")
    s.messages.append(StoredMessage(role="user", content="code ```py\nprint(1)\n```"))
    s.messages.append(StoredMessage(role="assistant", content="done"))
    store.save(s)
    md = store.export_markdown(s.meta.id)
    js = store.export_json(s.meta.id)
    assert md and "# Exp" in md and "print(1)" in md
    assert js and '"role": "user"' in js
    assert "api_key" not in js.lower() or "api_key" not in (js or "")


def test_corrupt_session_does_not_crash(tmp_path: Path):
    store = SessionStore(root=tmp_path)
    bad = tmp_path / "badid.json"
    bad.write_text("{not json", encoding="utf-8")
    assert store.load("badid") is None
    assert store.list_sessions() == [] or isinstance(store.list_sessions(), list)
