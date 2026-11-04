"""OpenCode-style TUI smoke tests (single column, command semantics)."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

pytest.importorskip("textual")

from hex_cli.providers.base import ChatMessage
from hex_cli.tui.app import HexApp
from hex_cli.tui.widgets.dialogs import CommandDialog


def test_single_column_compose(tmp_path: Path):
    async def _run():
        app = HexApp(workspace=tmp_path)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause(0.2)
            assert app.query_one("#top-header")
            assert app.query_one("#timeline")
            assert app.query_one("#composer-box")
            assert app.query_one("#composer-meta")
            assert app.query_one("#bottom-status")

    asyncio.run(_run())


def test_header_meta_real_numbers(tmp_path: Path):
    async def _run():
        app = HexApp(workspace=tmp_path)
        app.history = [ChatMessage(role="user", content="x" * 800)]
        app._ctx_chars = sum(len(m.content) for m in app.history)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause(0.2)
            app._refresh_all()
            from textual.widgets import Static

            stats = str(app.query_one("#hdr-stats", Static).render())
            assert "200" in stats
            assert "%" in stats
            assert "$0.00" in stats

    asyncio.run(_run())


def test_turn_renders_opencode_lines(tmp_path: Path):
    async def _run():
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "a.py").write_text("print(1)\n")
        app = HexApp(workspace=tmp_path)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause(0.2)
            box = app.query_one("#composer-box")
            box.value = "LIST src"
            await pilot.press("enter")
            for _ in range(60):
                await pilot.pause(0.2)
                if not app._busy:
                    break
            await pilot.pause(0.3)
            assert app._busy is False
            assert app.session.title == "LIST src"

    asyncio.run(_run())


def test_slash_command_unknown_note(tmp_path: Path):
    async def _run():
        app = HexApp(workspace=tmp_path)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause(0.2)
            box = app.query_one("#composer-box")
            box.value = "/definitelynotacommand"
            await pilot.press("enter")
            await pilot.pause(0.3)
            assert app._busy is False

    asyncio.run(_run())


def test_undo_removes_last_exchange(tmp_path: Path):
    async def _run():
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "a.py").write_text("print(1)\n")
        app = HexApp(workspace=tmp_path)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause(0.2)

            async def turn(text):
                box = app.query_one("#composer-box")
                box.value = text
                await pilot.press("enter")
                for _ in range(60):
                    await pilot.pause(0.2)
                    if not app._busy:
                        break
                await pilot.pause(0.2)

            await turn("LIST src")
            hist_before = len(app.history)
            assert hist_before >= 3
            app.action_command("undo")
            await pilot.pause(0.4)
            assert not any(m.role == "user" for m in app.history)
            assert len(app.history) < hist_before

    asyncio.run(_run())


def test_plan_mode_denies_writes(tmp_path: Path):
    async def _run():
        app = HexApp(workspace=tmp_path)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause(0.2)
            app.action_cycle_mode()
            await pilot.pause(0.2)
            assert app._agent_mode == "plan"
            res = app.tools.execute("write_file", {"path": "x.txt", "content": "hi"})
            assert res.ok is False
            assert "permission denied" in res.error

    asyncio.run(_run())


def test_command_dialog_dismisses(tmp_path: Path):
    async def _run():
        app = HexApp(workspace=tmp_path)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause(0.2)
            app.push_screen(CommandDialog())
            await pilot.pause(0.3)
            await pilot.press("escape")
            await pilot.pause(0.3)
            assert app.screen.__class__.__name__ != "CommandDialog"

    asyncio.run(_run())
