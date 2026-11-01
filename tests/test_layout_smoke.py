"""Layout / welcome smoke without full interactive terminal."""
from hex_cli.tui.widgets.chat import ChatLog
from hex_cli.tui.theme import HEX_CSS


def test_welcome_has_branding():
    w = ChatLog._welcome_markup()
    assert "HEX" in w
    assert "NeonBuild" in w
    assert "Powered by HEX" in w


def test_css_defines_sidebar_and_composer():
    assert "#sidebar" in HEX_CSS
    assert "#composer" in HEX_CSS or "#prompt-input" in HEX_CSS
    assert ".tool-card" in HEX_CSS
