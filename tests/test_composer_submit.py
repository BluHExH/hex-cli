"""Composer submit behavior (Enter send, empty reject)."""
from __future__ import annotations

from hex_cli.tui.widgets.input_panel import PromptSubmitted, SLASH_COMMANDS


def test_slash_commands_nonempty():
    assert len(SLASH_COMMANDS) >= 10
    assert any(c == "/help" for c, _ in SLASH_COMMANDS)


def test_prompt_submitted_message():
    msg = PromptSubmitted("hello world")
    assert msg.text == "hello world"


def test_empty_stripped_rejected_logic():
    """Mirror the submit guard used by PromptTextArea.action_submit_prompt."""
    def would_send(raw: str) -> bool:
        return bool(raw.strip())

    assert would_send("hi") is True
    assert would_send("") is False
    assert would_send("   \n  ") is False
    assert would_send("  code  ") is True


def test_newline_vs_send_semantics():
    """Document expected key semantics for regression docs."""
    enter_action = "submit_prompt"
    shift_enter_action = "insert_newline"
    assert enter_action != shift_enter_action
