"""Activity bar phase labels and idle behavior."""
from hex_cli.tui.widgets.activity_bar import PHASE_LABELS


def test_phase_labels_cover_common_tools():
    for key in ("thinking", "read_file", "write_file", "run_command", "completed"):
        assert key in PHASE_LABELS
        assert PHASE_LABELS[key]


def test_idle_label_empty():
    assert PHASE_LABELS["idle"] == ""


def test_welcome_contains_branding():
    from hex_cli.tui.widgets.chat import ChatLog
    w = ChatLog._welcome_markup()
    assert "HEX" in w
    assert "NeonBuild" in w
    assert "Powered by HEX" in w
