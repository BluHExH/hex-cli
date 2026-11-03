"""Exact-structure theme derived from the reference workspace screenshot.

Terminal/Textual cannot render true gradients or anti-aliased avatars; colors,
column ratios, and hierarchy follow the reference as closely as possible.
"""

HEX_THEME_CSS = """
/* Reference palette (sampled from dark OpenCode-style workspace) */
$bg: #0b0e14;
$bg-elev: #0f131a;
$panel: #0e1219;
$panel-2: #12171f;
$border: #1a2230;
$border-hi: #2a3548;
$text: #e6edf5;
$muted: #7d8da6;
$faint: #5c6b82;
$accent: #7c6cf0;
$accent-soft: #5b8def;
$user: #a8c7fa;
$ok: #3dd68c;
$warn: #e6c07b;
$chip: #151b26;

Screen {
    background: $bg;
    color: $text;
    layout: vertical;
}

/* ===== TOP HEADER (full width, single row) ===== */
#top-header {
    dock: top;
    height: 1;
    background: #080a0f;
    color: $muted;
    padding: 0 1;
    border-bottom: solid $border;
}

/* ===== MAIN BODY: 3 columns ===== */
#body {
    height: 1fr;
    layout: horizontal;
}

/* Left ~22 chars content + padding ≈ reference left rail proportion */
#left-rail {
    width: 28;
    background: $panel;
    border-right: solid $border;
    padding: 1 1 0 1;
    scrollbar-size: 1 1;
}

#center {
    width: 1fr;
    background: $bg;
    layout: vertical;
}

/* Right rail similar width to left */
#right-rail {
    width: 32;
    background: $panel;
    border-left: solid $border;
    padding: 1 1 0 1;
    scrollbar-size: 1 1;
}

#left-rail.collapsed, #right-rail.collapsed {
    width: 0;
    min-width: 0;
    padding: 0;
    border: none;
}

/* ===== Session tab strip ===== */
#session-tabs {
    height: 1;
    background: $bg-elev;
    border-bottom: solid $border;
    padding: 0 1;
    color: $muted;
}

/* ===== Conversation ===== */
#timeline {
    height: 1fr;
    background: $bg;
    padding: 1 2;
    scrollbar-background: $bg;
    scrollbar-color: $border-hi;
}

/* ===== Composer block (bottom of center) ===== */
#composer-dock {
    height: 6;
    background: $bg-elev;
    border-top: solid $border;
    padding: 1 2;
    layout: vertical;
}

#composer-box {
    height: 3;
    background: $chip;
    border: solid $border-hi;
    padding: 0 1;
    color: $text;
}

#composer-box:focus {
    border: solid $accent;
}

#composer-toolbar {
    height: 1;
    color: $muted;
    padding: 0 1;
    margin-top: 0;
}

/* ===== Bottom app status ===== */
#bottom-status {
    dock: bottom;
    height: 1;
    background: #07090d;
    color: $muted;
    padding: 0 1;
    border-top: solid $border;
}

/* utility */
.muted { color: $muted; }
.ok { color: $ok; }
.accent { color: $accent; }
"""
