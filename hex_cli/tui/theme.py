"""Central HEX TUI design tokens (Textual CSS variables)."""

HEX_THEME_CSS = """
/* === HEX design tokens === */
$hex-bg: #0b0f14;
$hex-bg-elevated: #111820;
$hex-bg-panel: #0e141c;
$hex-border: #1e2a38;
$hex-border-focus: #7c6aef;
$hex-text: #e6edf3;
$hex-muted: #8b9bb0;
$hex-accent: #a78bfa;
$hex-accent-2: #38bdf8;
$hex-user: #7dd3fc;
$hex-assistant: #c4b5fd;
$hex-tool: #fbbf24;
$hex-error: #f87171;
$hex-ok: #34d399;
$hex-surface: #151c27;

Screen {
    background: $hex-bg;
    color: $hex-text;
}

#app-header {
    dock: top;
    height: 3;
    background: $hex-bg-elevated;
    border-bottom: solid $hex-border;
    padding: 0 1;
}

#app-header .brand {
    color: $hex-accent;
    text-style: bold;
}

#app-header .meta {
    color: $hex-muted;
}

#main-row {
    height: 1fr;
}

#sidebar {
    width: 28;
    background: $hex-bg-panel;
    border-right: solid $hex-border;
    padding: 1 1;
}

#sidebar.collapsed {
    width: 0;
    padding: 0;
    border: none;
}

#sidebar .section-title {
    color: $hex-accent;
    text-style: bold;
    margin-top: 1;
}

#sidebar .muted {
    color: $hex-muted;
}

#content-col {
    width: 1fr;
}

#timeline {
    height: 1fr;
    padding: 1 2;
    background: $hex-bg;
    scrollbar-background: $hex-bg;
    scrollbar-color: $hex-border;
}

#home-panel {
    height: 1fr;
    padding: 2 3;
    background: $hex-bg;
}

#home-panel .hero {
    color: $hex-accent;
    text-style: bold;
}

#home-panel .welcome {
    color: $hex-text;
    margin-top: 1;
}

#home-panel .hint {
    color: $hex-muted;
    margin-top: 1;
}

#composer-wrap {
    dock: bottom;
    height: auto;
    min-height: 5;
    max-height: 12;
    background: $hex-bg-elevated;
    border-top: solid $hex-border;
    padding: 0 1 1 1;
}

#composer {
    height: 3;
    min-height: 3;
    background: $hex-surface;
    border: solid $hex-border;
    padding: 0 1;
}

#composer:focus {
    border: solid $hex-border-focus;
}

#status-bar {
    dock: bottom;
    height: 1;
    background: #070a0e;
    color: $hex-muted;
    padding: 0 1;
}

.msg-user {
    margin: 1 0;
    color: $hex-user;
}

.msg-assistant {
    margin: 1 0;
    color: $hex-text;
}

.msg-tool {
    margin: 0 0;
    color: $hex-tool;
    background: $hex-surface;
    padding: 0 1;
    border-left: tall $hex-tool;
}

.msg-error {
    color: $hex-error;
    margin: 1 0;
}

.msg-system {
    color: $hex-muted;
    text-style: italic;
}

.tool-header {
    color: $hex-tool;
    text-style: bold;
}

.tool-body {
    color: $hex-muted;
}
"""
