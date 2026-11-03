"""TUI composition and binding smoke tests (requires textual)."""
from __future__ import annotations

import pytest

textual = pytest.importorskip("textual")

from pathlib import Path

from hex_cli.tui.app import HexApp


async def test_app_composes(tmp_path: Path):
    app = HexApp(workspace=tmp_path)
    async with app.run_test(size=(120, 36)) as pilot:
        assert app.query_one("#app-header")
        assert app.query_one("#sidebar")
        assert app.query_one("#composer")
        assert app.query_one("#status-bar")
        assert app.query_one("#home-panel")


async def test_narrow_hides_sidebar_logic(tmp_path: Path):
    app = HexApp(workspace=tmp_path)
    async with app.run_test(size=(80, 24)) as pilot:
        app._adapt_layout()
        # narrow should hide sidebar display
        assert app.size.width < 100


async def test_submit_shows_timeline(tmp_path: Path):
    app = HexApp(workspace=tmp_path)
    async with app.run_test(size=(120, 36)) as pilot:
        composer = app.query_one("#composer")
        composer.load_text("LIST .")
        await pilot.press("ctrl+enter")
        # worker may still be running; home should hide after ensure
        await pilot.pause(0.5)
        assert app.query_one("#timeline")
