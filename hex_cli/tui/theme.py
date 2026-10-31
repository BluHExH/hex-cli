"""HEX TUI colour theme and CSS — professional dark terminal aesthetic."""

from __future__ import annotations

HEX_CSS = """
Screen {
    background: #0a0e14;
    color: #e6edf3;
}

#header {
    dock: top;
    height: 3;
    background: #0d1117;
    border-bottom: tall #21262d;
    padding: 0 1;
    layout: horizontal;
}

#header-brand {
    width: 16;
    color: #c084fc;
    text-style: bold;
    content-align: left middle;
}

#header-project {
    width: 1fr;
    color: #8b949e;
    content-align: left middle;
}

#header-provider {
    width: auto;
    color: #58a6ff;
    content-align: right middle;
    padding-right: 1;
}

#header-status {
    width: 12;
    content-align: right middle;
}

.status-ok { color: #3fb950; }
.status-busy { color: #d29922; }
.status-err { color: #f85149; }

#sidebar {
    dock: left;
    width: 26;
    background: #0d1117;
    border-right: tall #21262d;
}

#sidebar.collapsed {
    width: 0;
    border: none;
    display: none;
}

.sidebar-section {
    color: #6e7681;
    text-style: bold;
    padding: 1 1 0 1;
}

.sidebar-item {
    padding: 0 1;
    height: 1;
    color: #c9d1d9;
}

.sidebar-item:hover {
    background: #161b22;
    color: #e6edf3;
}

.sidebar-item.-active {
    background: #21262d;
    color: #c084fc;
    text-style: bold;
}

.sidebar-meta {
    padding: 0 1;
    color: #8b949e;
    height: 1;
}

#chat-container {
    width: 1fr;
    height: 1fr;
    background: #0a0e14;
}

#chat-log {
    height: 1fr;
    padding: 1 2;
    scrollbar-background: #0a0e14;
    scrollbar-color: #30363d;
}

.message {
    margin: 0 0 1 0;
    padding: 0 1;
}

.message-user {
    border-left: thick #58a6ff;
    background: #0d1117;
    padding: 1 1;
}

.message-assistant {
    border-left: thick #c084fc;
    padding: 1 1;
}

.message-tool {
    border-left: thick #d29922;
    color: #e3b341;
    padding: 0 1;
}

.message-error {
    border-left: thick #f85149;
    color: #ffa198;
    background: #1c0a0a;
    padding: 1 1;
}

.message-system {
    color: #8b949e;
    padding: 0 1;
}

.message-status {
    color: #6e7681;
    text-style: italic;
}

.message-welcome {
    color: #8b949e;
    padding: 2 2;
    text-align: center;
}

#input-wrap {
    dock: bottom;
    height: auto;
    max-height: 14;
    background: #0d1117;
    border-top: tall #21262d;
    padding: 0 1;
}

#input-bar {
    height: 1;
    color: #6e7681;
    padding: 0 1;
}

#prompt-input {
    height: 4;
    min-height: 3;
    max-height: 8;
    background: #161b22;
    border: tall #30363d;
    padding: 0 1;
}

#prompt-input:focus {
    border: tall #c084fc;
}

#cmd-suggest {
    height: auto;
    max-height: 8;
    background: #161b22;
    border: tall #30363d;
    padding: 0 1;
    display: none;
}

#cmd-suggest.visible {
    display: block;
}

#footer-bar {
    dock: bottom;
    height: 1;
    background: #010409;
    color: #6e7681;
    padding: 0 1;
    border-top: solid #21262d;
}

.dialog {
    width: 72;
    max-width: 90%;
    height: auto;
    max-height: 80%;
    background: #161b22;
    border: tall #30363d;
    padding: 1 2;
}

.dialog-title {
    text-style: bold;
    color: #c084fc;
    margin-bottom: 1;
}

.dialog-body {
    color: #c9d1d9;
    margin-bottom: 1;
    height: auto;
    max-height: 30;
}

.dialog-list {
    height: 16;
    min-height: 8;
    border: tall #21262d;
    background: #0d1117;
    margin-bottom: 1;
}

.dialog-buttons {
    height: 3;
    align: right middle;
}
"""

HEX_LOGO = """
██╗  ██╗███████╗██╗  ██╗
██║  ██║██╔════╝╚██╗██╔╝
███████║█████╗   ╚███╔╝
██╔══██║██╔══╝   ██╔██╗
██║  ██║███████╗██╔╝ ██╗
╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
"""
