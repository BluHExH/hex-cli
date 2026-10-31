"""Regression: chat widget IDs must stay unique across clear/new-session."""

from __future__ import annotations

from pathlib import Path

import pytest

from hex_cli.tui.state import ChatEntry, SessionState
from hex_cli.tui.widgets.chat import ChatLog, _next_msg_id


def test_next_msg_id_unique() -> None:
    ids = {_next_msg_id() for _ in range(50)}
    assert len(ids) == 50


def test_session_state_new_and_clear() -> None:
    st = SessionState(project_root=Path("."), provider_name="openrouter", model="x")
    assert len(st.sessions) == 1
    st.add("user", "hello")
    assert len(st.entries) == 1
    st.clear_conversation()
    assert len(st.entries) == 0
    s2 = st.new_session()
    assert len(st.sessions) == 2
    assert st.active_session_id == s2.id
    assert len(st.entries) == 0
    st.add("user", "in session 2")
    assert len(st.entries) == 1
    first = st.sessions[0].id
    assert st.switch_session(first)
    assert len(st.entries) == 0


def test_repeated_new_session_ids() -> None:
    st = SessionState(project_root=Path("."), provider_name="ollama", model="llama")
    ids = set()
    for _ in range(25):
        s = st.new_session()
        assert s.id not in ids
        ids.add(s.id)
    assert len(ids) == 25


@pytest.mark.asyncio
async def test_chatlog_clear_and_append_no_duplicate_ids() -> None:
    from textual.app import App, ComposeResult

    class Harness(App[None]):
        def compose(self) -> ComposeResult:
            yield ChatLog()

    app = Harness()
    async with app.run_test() as pilot:
        log = app.query_one(ChatLog)
        for i in range(20):
            log.clear_messages(banner=f"[dim]cleared {i}[/dim]")
            for j in range(3):
                log.append_entry(ChatEntry(kind="user", text=f"msg {i}-{j}"))
            log.append_entry(ChatEntry(kind="system", text=f"sys {i}"))
        ids = [c.id for c in log.children if c.id]
        assert len(ids) == len(set(ids)), f"duplicate ids: {ids}"


@pytest.mark.asyncio
async def test_chatlog_twenty_new_session_cycles() -> None:
    from textual.app import App, ComposeResult

    class Harness(App[None]):
        def compose(self) -> ComposeResult:
            yield ChatLog()

    app = Harness()
    async with app.run_test() as pilot:
        log = app.query_one(ChatLog)
        for n in range(20):
            log.clear_messages(banner=f"[bold]Session {n}[/]\n[dim]ready[/]")
            log.append_entry(ChatEntry(kind="system", text=f"New session {n}"))
            log.append_entry(ChatEntry(kind="user", text="hi"))
            log.append_entry(ChatEntry(kind="assistant", text="hello"))
        ids = [c.id for c in log.children if c.id]
        assert len(ids) == len(set(ids))
