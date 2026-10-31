"""Configurable HEX TUI themes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Theme:
    id: str
    name: str
    css: str


HEX_DARK = Theme(
    id="hex-dark",
    name="HEX Dark",
    css="",  # default from theme.py HEX_CSS
)

HEX_LIGHT = Theme(
    id="hex-light",
    name="HEX Light",
    css="""
Screen { background: #f6f8fa; color: #1f2328; }
#header { background: #ffffff; border-bottom: solid #d0d7de; }
#header-brand { color: #8250df; }
#header-project { color: #656d76; }
#header-provider { color: #0969da; }
#sidebar { background: #ffffff; border-right: solid #d0d7de; }
#sidebar-brand { color: #8250df; border-bottom: solid #d0d7de; }
.sidebar-section { color: #656d76; }
.sidebar-item { color: #1f2328; }
.sidebar-item:hover { background: #eaeef2; }
.sidebar-item.-active { background: #fbefff; color: #8250df; border-left: thick #8250df; }
.sidebar-meta { color: #656d76; }
#main-workspace, #chat-container, #chat-log { background: #f6f8fa; }
.message-user { background: #ffffff; border-left: thick #0969da; }
.message-assistant { background: #ffffff; border-left: thick #8250df; }
.message-tool { background: #fff8c5; border-left: thick #9a6700; color: #7d4e00; }
.message-error { background: #ffebe9; border-left: thick #cf222e; color: #a40e26; }
#composer { background: #ffffff; border-top: solid #d0d7de; }
#prompt-input { background: #f6f8fa; border: tall #d0d7de; color: #1f2328; }
#prompt-input:focus { border: tall #8250df; }
#footer-bar { background: #f6f8fa; border-top: solid #d0d7de; color: #656d76; }
#btn-new-session { background: #f6f8fa; color: #8250df; border: tall #d0d7de; }
""",
)

HIGH_CONTRAST = Theme(
    id="high-contrast",
    name="High Contrast",
    css="""
Screen { background: #000000; color: #ffffff; }
#header { background: #000000; border-bottom: solid #ffffff; }
#header-brand { color: #ffff00; }
#sidebar { background: #000000; border-right: solid #ffffff; }
.sidebar-item.-active { background: #333333; color: #ffff00; border-left: thick #ffff00; }
#composer { background: #000000; border-top: solid #ffffff; }
#prompt-input { background: #111111; border: tall #ffffff; color: #ffffff; }
#prompt-input:focus { border: tall #ffff00; }
.message-user { border-left: thick #00ffff; }
.message-assistant { border-left: thick #ffff00; }
""",
)

THEMES: Dict[str, Theme] = {
    HEX_DARK.id: HEX_DARK,
    HEX_LIGHT.id: HEX_LIGHT,
    HIGH_CONTRAST.id: HIGH_CONTRAST,
}


def list_themes() -> list[Theme]:
    return list(THEMES.values())


def get_theme(theme_id: str) -> Theme:
    return THEMES.get(theme_id, HEX_DARK)
