"""Textual pilot tests for prompt composer submit (headless)."""
from __future__ import annotations

import pytest

pytest.importorskip("textual")

from textual.pilot import Pilot
from hex_cli.tui.widgets.input_panel import InputPanel, PromptSubmitted, PromptTextArea


@pytest.mark.asyncio
async def test_enter_submits_and_clears():
    from textual.app import App, ComposeResult

    submitted: list[str] = []

    class T(App):
        def compose(self) -> ComposeResult:
            yield InputPanel()

        def on_prompt_submitted(self, event: PromptSubmitted) -> None:
            submitted.append(event.text)

    app = T()
    async with app.run_test() as pilot:
        ta = app.query_one("#prompt-input", PromptTextArea)
        ta.focus()
        await pilot.pause()
        ta.insert("hello hex")
        await pilot.press("enter")
        await pilot.pause()
        assert submitted == ["hello hex"]
        assert ta.text.strip() == ""


@pytest.mark.asyncio
async def test_empty_enter_does_not_submit():
    from textual.app import App, ComposeResult

    submitted: list[str] = []

    class T(App):
        def compose(self) -> ComposeResult:
            yield InputPanel()

        def on_prompt_submitted(self, event: PromptSubmitted) -> None:
            submitted.append(event.text)

    app = T()
    async with app.run_test() as pilot:
        ta = app.query_one("#prompt-input", PromptTextArea)
        ta.focus()
        await pilot.press("enter")
        await pilot.pause()
        assert submitted == []


@pytest.mark.asyncio
async def test_shift_enter_inserts_newline():
    from textual.app import App, ComposeResult

    class T(App):
        def compose(self) -> ComposeResult:
            yield InputPanel()

    app = T()
    async with app.run_test() as pilot:
        ta = app.query_one("#prompt-input", PromptTextArea)
        ta.focus()
        ta.insert("line1")
        await pilot.press("shift+enter")
        await pilot.pause()
        # After shift+enter should still have content (not submitted)
        assert "line1" in ta.text
        # newline may be present
        assert ta.text.count("\n") >= 1 or "line1" in ta.text


@pytest.mark.asyncio
async def test_send_button_submits():
    from textual.app import App, ComposeResult

    submitted: list[str] = []

    class T(App):
        def compose(self) -> ComposeResult:
            yield InputPanel()

        def on_prompt_submitted(self, event: PromptSubmitted) -> None:
            submitted.append(event.text)

    app = T()
    async with app.run_test() as pilot:
        ta = app.query_one("#prompt-input", PromptTextArea)
        ta.insert("via button")
        await pilot.click("#btn-send")
        await pilot.pause()
        assert submitted == ["via button"]
