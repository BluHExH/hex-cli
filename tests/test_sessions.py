from pathlib import Path

from hex_cli.sessions.store import SessionStore


def test_session_roundtrip(tmp_path: Path):
    store = SessionStore(tmp_path)
    s = store.create("t1")
    s.messages.append({"role": "user", "content": "hi"})
    store.save(s)
    loaded = store.load(s.id)
    assert loaded.messages[0]["content"] == "hi"
    assert any(x.id == s.id for x in store.list())
