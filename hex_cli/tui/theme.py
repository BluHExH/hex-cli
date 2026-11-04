"""HEX TUI theme — OpenCode v2 look: black canvas, subtle blocks, single blue accent."""

HEX_THEME_CSS = """
$bg: #050506;
$block: #121318;
$block-hi: #14151c;
$panel: #10131a;
$border: #22262f;
$text: #e8eaef;
$muted: #7d8590;
$accent: #4d9eff;
$danger: #e05c5c;

Screen {
    background: $bg;
    color: $text;
}

#top-header {
    dock: top;
    height: 1;
    background: $block-hi;
    padding: 0 1;
}

#hdr-title {
    height: 1;
    width: 1fr;
    color: $text;
}

#hdr-stats {
    height: 1;
    width: auto;
    color: $muted;
    text-align: right;
}

#body {
    height: 1fr;
    layout: vertical;
}

#timeline {
    height: 1fr;
    background: $bg;
    padding: 0 2;
    scrollbar-size: 1 1;
    scrollbar-color: #2a2f3a transparent;
}

#composer-dock {
    dock: bottom;
    height: auto;
    background: $block;
    border-left: heavy $accent;
    padding: 0 1;
}

#command-hints {
    display: none;
    height: auto;
    max-height: 7;
    color: $muted;
    padding: 0 0 0 1;
}

#composer-box {
    height: 1;
    border: none;
    padding: 0 1;
    background: transparent;
    color: $text;
}

#composer-meta {
    height: 1;
    padding: 0 1;
    color: $muted;
}

#bottom-status {
    dock: bottom;
    height: 1;
    background: $bg;
    color: $muted;
    padding: 0 1;
}
"""
