
from hex_cli.tui.widgets.chat import ChatLog

def test_welcome_is_minimal_opencode_style():
    text = ChatLog._welcome_markup()
    assert "How can I help you today" in text
    assert "HEX" in text or "NeonBuild" in text
    assert "██" not in text  # no big ASCII logo
