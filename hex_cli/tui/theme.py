"""HEX TUI colour theme and CSS."""

from __future__ import annotations

# Textual CSS for the HEX app — dark, professional, OpenCode-inspired spacing.
HEX_CSS = """
/* ---- Global ---- */
Screen {
    background: #0d1117;
    color: #e6edf3;
}

/* ---- Header ---- */
#header {
    dock: top;
    height: 3;
    background: #161b22;
    border-bottom: solid #30363d;
    padding: 0 1;
}

#header-brand {
    width: 14;
    color: #c084fc;
    text-style: bold;
}

#header-project {
    width: 1fr;
    color: #8b949e;
}

#header-provider {
    width: auto;
    color: #58a6ff;
    text-align: right;
}

#header-status {
    width: 12;
    text-align: right;
}

.status-ok { color: #3fb950; }
.status-busy { color: #d29922; }
.status-err { color: #f85149; }

/* ---- Sidebar ---- */
#sidebar {
    dock: left;
    width: 28;
    background: #0d1117;
    border-right: solid #30363d;
    padding: 1 0;
}

#sidebar.collapsed {
    width: 0;
    border: none;
    padding: 0;
}

.sidebar-title {
    color: #8b949e;
    text-style: bold;
    padding: 0 1;
    margin-top: 1;
}

.sidebar-item {
    padding: 0 1;
    height: 1;
    color: #e6edf3;
}

.sidebar-item:hover {
    background: #21262d;
}

.sidebar-item.-selected {
    background: #21262d;
    color: #c084fc;
}

.sidebar-muted {
    color: #8b949e;
    padding: 0 1;
}

/* ---- Chat ---- */
#chat-container {
    width: 1fr;
    height: 1fr;
    background: #0d1117;
}

#chat-log {
    height: 1fr;
    padding: 1 2;
    scrollbar-background: #0d1117;
    scrollbar-color: #30363d;
}

.message {
    margin-bottom: 1;
    padding: 0 1;
}

.message-user {
    border-left: thick #c084fc;
    background: #161b22;
}

.message-assistant {
    border-left: thick #58a6ff;
}

.message-tool {
    border-left: thick #3fb950;
    color: #8b949e;
}

.message-error {
    border-left: thick #f85149;
    color: #f85149;
}

.message-system {
    color: #8b949e;
    text-style: italic;
}

.message-status {
    color: #d29922;
}

.msg-label {
    text-style: bold;
    color: #8b949e;
}

/* ---- Input ---- */
#input-panel {
    dock: bottom;
    height: auto;
    min-height: 5;
    max-height: 12;
    background: #161b22;
    border-top: solid #30363d;
    padding: 0 1 1 1;
}

#input-hints {
    height: 1;
    color: #8b949e;
    padding: 0 1;
}

#prompt-input {
    height: auto;
    min-height: 3;
    max-height: 8;
    background: #0d1117;
    border: solid #30363d;
    padding: 0 1;
}

#prompt-input:focus {
    border: solid #c084fc;
}

/* ---- Footer ---- */
#footer-bar {
    dock: bottom;
    height: 1;
    background: #161b22;
    color: #8b949e;
    padding: 0 1;
}

/* ---- Dialogs ---- */
DialogScreen {
    align: center middle;
    background: rgba(13, 17, 23, 0.72);
}

.dialog {
    width: 64;
    max-width: 90%;
    height: auto;
    max-height: 80%;
    background: #161b22;
    border: solid #c084fc;
    padding: 1 2;
}

.dialog-title {
    text-style: bold;
    color: #c084fc;
    margin-bottom: 1;
}

.dialog-body {
    margin-bottom: 1;
    height: auto;
    max-height: 20;
}

.dialog-list {
    height: 12;
    border: solid #30363d;
}

ListItem {
    padding: 0 1;
}

ListItem:hover {
    background: #21262d;
}

ListView > ListItem.-highlighted {
    background: #30363d;
}

.dialog-buttons {
    height: 3;
    align: right middle;
}

/* ---- Welcome ---- */
#welcome {
    width: 100%;
    height: 100%;
    align: center middle;
}

.welcome-box {
    width: 72;
    max-width: 90%;
    height: auto;
    border: solid #30363d;
    background: #161b22;
    padding: 2 3;
}

.welcome-logo {
    text-align: center;
    color: #c084fc;
    text-style: bold;
}

.welcome-sub {
    text-align: center;
    color: #8b949e;
    margin-bottom: 1;
}

.welcome-hints {
    color: #e6edf3;
}
"""
