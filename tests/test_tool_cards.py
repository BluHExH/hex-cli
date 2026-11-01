"""Tool card state machine and update-in-place behavior."""
from __future__ import annotations

from hex_cli.tui.widgets.tool_card import (
    ToolCard,
    ToolCardState,
    status_from_string,
    TOOL_TITLES,
)


def test_status_from_string_mapping():
    assert status_from_string("running") == ToolCardState.RUNNING
    assert status_from_string("ok") == ToolCardState.COMPLETED
    assert status_from_string("error") == ToolCardState.FAILED
    assert status_from_string("skipped") == ToolCardState.DENIED
    assert status_from_string("cancelled") == ToolCardState.CANCELLED


def test_tool_titles_cover_core_tools():
    for name in ("read_file", "write_file", "edit_file", "run_command", "git_status"):
        assert name in TOOL_TITLES


def test_tool_card_progresses_without_duplicate_state_loss():
    card = ToolCard("read_file", detail="src/main.py")
    assert card.state == ToolCardState.RUNNING
    card.set_status("running", detail="src/main.py")
    assert card.state == ToolCardState.RUNNING
    card.set_status("ok", output="print('hi')")
    assert card.state == ToolCardState.COMPLETED
    assert "print" in card.output
    card.toggle()
    assert card.expanded is True
    card.toggle()
    assert card.expanded is False


def test_failed_and_cancelled():
    c = ToolCard("run_command", detail="pytest")
    c.set_status("error", error="exit 1")
    assert c.state == ToolCardState.FAILED
    c2 = ToolCard("run_command", detail="sleep")
    c2.set_status("cancelled")
    assert c2.state == ToolCardState.CANCELLED
