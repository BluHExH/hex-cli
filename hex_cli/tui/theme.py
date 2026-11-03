"""HEX TUI theme — dark workspace matching professional coding-agent density."""

HEX_THEME_CSS = """
$bg: #0c0f14;
$panel: #10151c;
$panel-2: #141a22;
$border: #1c2430;
$border-soft: #243041;
$text: #e8eef7;
$muted: #8b9bb0;
$accent: #8b7cf7;
$accent-2: #5b8def;
$user: #9ecbff;
$ok: #3ecf8e;
$warn: #e6b84d;
$err: #f07178;
$chip: #1a2230;

Screen { background: $bg; color: $text; }

/* —— Header —— */
#top-header {
    dock: top;
    height: 1;
    background: #0a0d12;
    color: $muted;
    padding: 0 1;
    border-bottom: solid $border;
}

/* —— Body three columns —— */
#body {
    height: 1fr;
}

#left-rail {
    width: 26;
    background: $panel;
    border-right: solid $border;
    padding: 1 1;
}

#center {
    width: 1fr;
    background: $bg;
}

#right-rail {
    width: 30;
    background: $panel;
    border-left: solid $border;
    padding: 1 1;
}

#left-rail.collapsed, #right-rail.collapsed {
    width: 0;
    padding: 0;
    border: none;
}

.rail-title {
    color: $accent;
    text-style: bold;
    margin-bottom: 0;
}

.rail-muted { color: $muted; }
.rail-item { color: $text; }
.rail-ok { color: $ok; }

/* —— Session tabs —— */
#session-tabs {
    height: 1;
    background: $panel-2;
    border-bottom: solid $border;
    padding: 0 1;
    color: $muted;
}

/* —— Timeline —— */
#timeline {
    height: 1fr;
    padding: 1 2;
    scrollbar-background: $bg;
    scrollbar-color: $border-soft;
}

/* —— Composer —— */
#composer-dock {
    height: auto;
    min-height: 5;
    max-height: 10;
    background: $panel-2;
    border-top: solid $border;
    padding: 0 1 1 1;
}

#composer-box {
    height: 3;
    background: $chip;
    border: solid $border-soft;
    padding: 0 1;
}

#composer-box:focus-within {
    border: solid $accent;
}

#composer-toolbar {
    height: 1;
    color: $muted;
    padding: 0 1;
}

/* —— Status —— */
#bottom-status {
    dock: bottom;
    height: 1;
    background: #080a0e;
    color: $muted;
    padding: 0 1;
    border-top: solid $border;
}

/* —— Welcome card —— */
.welcome-card {
    background: $panel-2;
    border: solid $border-soft;
    padding: 1 2;
    margin: 1 0;
}

/* —— Tool card —— */
.tool-card {
    background: $panel-2;
    border-left: tall $accent-2;
    padding: 0 1;
    margin: 0 0 1 0;
}
"""
