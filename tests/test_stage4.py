"""Stage 4: sessions, agents, streaming, tracker review, intelligence."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from hex_cli.agents import AgentKind, get_agent, list_agents
from hex_cli.changes.tracker import ChangeTracker
from hex_cli.intelligence.diagnostics import collect_basic_diagnostics
from hex_cli.intelligence.search import project_search
from hex_cli.sessions.store import SessionStore, StoredMessage, STORAGE_VERSION
from hex_cli.streaming.engine import StreamEngine, StreamEvent, StreamKind
from hex_cli.tools.registry import openai_tool_schemas, tool_names


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

def test_session_create_save_load_delete():
    with tempfile.TemporaryDirectory() as td:
        store = SessionStore(Path(td))
        s = store.create("Alpha", Path("/tmp/proj"), provider="ollama", model="llama", agent="build")
        assert s.meta.id
        assert s.version == STORAGE_VERSION
        store.append_message(s.meta.id, StoredMessage(role="user", content="hello"))
        store.append_message(s.meta.id, StoredMessage(role="assistant", content="world"))
        loaded = store.load(s.meta.id)
        assert loaded is not None
        assert len(loaded.messages) == 2
        assert loaded.messages[0].content == "hello"
        assert store.rename(s.meta.id, "Beta")
        loaded2 = store.load(s.meta.id)
        assert loaded2 and loaded2.meta.name == "Beta"
        assert store.delete(s.meta.id)
        assert store.load(s.meta.id) is None


def test_session_search_and_list():
    with tempfile.TemporaryDirectory() as td:
        store = SessionStore(Path(td))
        a = store.create("Auth refactor", Path("/p1"), agent="build")
        store.append_message(a.meta.id, StoredMessage(role="user", content="fix login"))
        b = store.create("Docs pass", Path("/p1"), agent="explore")
        store.append_message(b.meta.id, StoredMessage(role="user", content="readme"))
        hits = store.search("auth")
        assert any(h.id == a.meta.id for h in hits)
        listed = store.list_sessions(project_root="/p1")
        assert len(listed) >= 2


def test_session_no_secrets_in_meta():
    with tempfile.TemporaryDirectory() as td:
        store = SessionStore(Path(td))
        s = store.create("S", Path("."), provider="x", model="y")
        # Manually inject a secret-like field then re-save through store
        data = json.loads((Path(td) / f"{s.meta.id}.json").read_text())
        data["meta"]["api_key"] = "sk-secret"
        (Path(td) / f"{s.meta.id}.json").write_text(json.dumps(data))
        loaded = store.load(s.meta.id)
        assert loaded
        # Re-save should strip key-like fields
        store.save(loaded)
        data2 = json.loads((Path(td) / f"{s.meta.id}.json").read_text())
        assert "api_key" not in data2.get("meta", {})


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

def test_agent_profiles_exist():
    agents = list_agents()
    ids = {a.id for a in agents}
    assert ids == {"build", "plan", "explore", "general"}


def test_plan_agent_is_readonly():
    plan = get_agent(AgentKind.PLAN)
    assert plan.plan_only
    assert "write_file" not in plan.allowed_tools
    assert "run_command" not in plan.allowed_tools
    assert "read_file" in plan.allowed_tools


def test_build_agent_has_write_tools():
    build = get_agent("build")
    assert "write_file" in build.allowed_tools
    assert "edit_file" in build.allowed_tools
    assert "git_commit" in build.allowed_tools


def test_tool_schemas_respect_allowlist():
    plan = get_agent(AgentKind.PLAN)
    schemas = openai_tool_schemas(plan.allowed_tools)
    names = {s["function"]["name"] for s in schemas}
    assert "read_file" in names
    assert "write_file" not in names


# ---------------------------------------------------------------------------
# Streaming
# ---------------------------------------------------------------------------

def test_stream_engine_text_and_finish():
    events: list[StreamEvent] = []
    engine = StreamEngine(on_event=events.append)
    engine.emit(StreamEvent(kind=StreamKind.TEXT_DELTA, text="Hel"))
    engine.emit(StreamEvent(kind=StreamKind.TEXT_DELTA, text="lo"))
    engine.emit(StreamEvent(kind=StreamKind.FINISH, finish_reason="stop"))
    assert engine.accumulated_text == "Hello"
    kinds = [e.kind for e in events]
    assert StreamKind.TEXT_DELTA in kinds
    assert StreamKind.FINISH in kinds


def test_stream_engine_cancel():
    events: list[StreamEvent] = []
    engine = StreamEngine(on_event=events.append)
    engine.cancel()
    engine.emit(StreamEvent(kind=StreamKind.TEXT_DELTA, text="x"))
    assert events == []


def test_stream_non_streaming_fallback():
    events: list[StreamEvent] = []
    engine = StreamEngine(on_event=events.append)
    engine.finalize_non_streaming("done", None)
    assert any(e.kind == StreamKind.FINISH for e in events)
    assert engine.accumulated_text == "done"


# ---------------------------------------------------------------------------
# ChangeTracker review
# ---------------------------------------------------------------------------

def test_tracker_accept_reject_and_external():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        f = root / "a.txt"
        f.write_text("v1", encoding="utf-8")
        tracker = ChangeTracker(root)
        tracker.record("a.txt", "modify", "v1", "v2")
        f.write_text("v2", encoding="utf-8")
        # External edit
        f.write_text("external", encoding="utf-8")
        ext = tracker.detect_external_modifications()
        assert any(e["path"] == "a.txt" for e in ext)
        # Reject should refuse when external
        res = tracker.reject_file("a.txt")
        assert res.get("ok") is False
        # Accept clears tracking
        f.write_text("v2", encoding="utf-8")
        # Re-sync: record again cleanly
        tracker.clear()
        tracker.record("a.txt", "modify", "v1", "v2")
        f.write_text("v2", encoding="utf-8")
        ok = tracker.accept_file("a.txt")
        assert ok["ok"]
        assert tracker.get_latest_for("a.txt") is None


def test_tracker_review_summary():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        tracker = ChangeTracker(root)
        tracker.record("x.py", "create", None, "print(1)\n")
        summary = tracker.review_summary()
        assert summary["file_count"] == 1
        assert "paths" in summary
        assert "external" in summary


# ---------------------------------------------------------------------------
# Intelligence
# ---------------------------------------------------------------------------

def test_diagnostics_python_syntax():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        bad = root / "bad.py"
        bad.write_text("def broken(\n", encoding="utf-8")
        diags = collect_basic_diagnostics(root, paths=["bad.py"])
        assert any(d.severity == "error" for d in diags)


def test_project_search_hits():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "mod.py").write_text("def hello_world():\n    return 42\n", encoding="utf-8")
        hits = project_search(root, "hello_world")
        assert len(hits) >= 1
        assert hits[0].path == "mod.py"


# ---------------------------------------------------------------------------
# Registry growth
# ---------------------------------------------------------------------------

def test_registry_has_git_tools():
    names = set(tool_names())
    for n in ("git_branches", "git_log", "git_stage", "git_commit", "git_checkout"):
        assert n in names
