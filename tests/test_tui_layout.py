"""Three-column TUI smoke tests."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

pytest.importorskip("textual")

from hex_cli.tui.app import HexApp


def test_three_column_compose(tmp_path: Path):
    async def _run():
        app = HexApp(workspace=tmp_path)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause(0.1)
            assert app.query_one("#top-header")
            assert app.query_one("#left-rail")
            assert app.query_one("#right-rail")
            assert app.query_one("#timeline")
            assert app.query_one("#composer-box")
            assert app.query_one("#bottom-status")

    asyncio.run(_run())


def test_narrow_hides_rails(tmp_path: Path):
    async def _run():
        app = HexApp(workspace=tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause(0.1)
            app._adapt()
            assert app.query_one("#left-rail").display is False
            assert app.query_one("#right-rail").display is False

    asyncio.run(_run())


def test_submit_turn_mock(tmp_path: Path):
    async def _run():
        app = HexApp(workspace=tmp_path)
        async with app.run_test(size=(140, 40)) as pilot:
            box = app.query_one("#composer-box")
            box.value = "LIST ."
            await pilot.press("enter")
            await pilot.pause(1.5)
            assert app._busy is False
            assert len(app._activities) >= 1

    asyncio.run(_run())
