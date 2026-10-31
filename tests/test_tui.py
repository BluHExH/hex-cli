"""Tests for HEX TUI Stage 1 components."""

from __future__ import annotations

from pathlib import Path

import pytest

from hex_cli.tui.state import ChatEntry, SessionState
from hex_cli.tui.app import FREE_MODEL_PRESETS, HexApp
from hex_cli.config import AppConfig, load_config


def test_session_state_add_and_clear(tmp_path: Path) -> None:
    st = SessionState(project_root=tmp_path, provider_name="openrouter", model="test")
    st.add("user", "hello")
    st.add("assistant", "hi")
    assert len(st.entries) == 2
    assert st.entries[0].kind == "user"
    st.clear_conversation()
    assert len(st.entries) == 0
    assert "cleared" in st.status_message.lower()


def test_chat_entry_meta() -> None:
    e = ChatEntry(kind="tool", text="read_file", meta={"status": "ok"})
    assert e.meta["status"] == "ok"


def test_free_model_presets_nonempty() -> None:
    assert len(FREE_MODEL_PRESETS) >= 5
    assert any(":free" in m for m in FREE_MODEL_PRESETS)
    assert "openrouter/free" in FREE_MODEL_PRESETS


def test_hex_app_constructs(tmp_path: Path) -> None:
    cfg = AppConfig()
    app = HexApp(tmp_path, cfg, model_override="test-model")
    assert app.state.model == "test-model"
    assert app.project_root == tmp_path.resolve()
    assert app.state.sidebar_visible is True


def test_hex_app_css_loaded(tmp_path: Path) -> None:
    cfg = AppConfig()
    app = HexApp(tmp_path, cfg)
    assert "header" in app.CSS.lower() or "#header" in app.CSS
    assert "sidebar" in app.CSS.lower() or "#sidebar" in app.CSS


@pytest.mark.asyncio
async def test_hex_app_compose(tmp_path: Path) -> None:
    """Smoke-test that the app can mount in a headless pilot."""
    cfg = AppConfig()
    app = HexApp(tmp_path, cfg)
    async with app.run_test() as pilot:
        # Header and chat should exist
        assert app.query("HeaderBar") or app.query("#header")
        assert app.query("ChatLog") or app.query("#chat-log")
        assert app.query("InputPanel") or app.query("#input-panel")
        # Toggle sidebar action should not crash
        app.action_toggle_sidebar()
        assert app.state.sidebar_visible is False
        app.action_toggle_sidebar()
        assert app.state.sidebar_visible is True
        # Clear chat
        app.action_clear_chat()
        assert len(app.state.entries) == 0
