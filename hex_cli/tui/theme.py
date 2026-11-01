"""HEX TUI theme — professional dark coding-agent aesthetic."""

from __future__ import annotations

HEX_CSS = """

Screen {
    background: #0b0f14;
    color: #e6edf3;
}

/* ── Top chrome ─────────────────────────────────────────── */
#header {
    dock: top;
    height: 1;
    background: #0b0f14;
    border-bottom: solid #1c2333;
    padding: 0 1;
    layout: horizontal;
}

#header-brand {
    width: 10;
    color: #a78bfa;
    text-style: bold;
    content-align: left middle;
}

#header-project {
    width: 1fr;
    color: #7d8590;
    content-align: left middle;
}

#header-provider {
    width: auto;
    color: #58a6ff;
    content-align: right middle;
    padding-right: 1;
}

#header-status {
    width: 14;
    content-align: right middle;
}

.status-ok { color: #3fb950; }
.status-busy { color: #d29922; }
.status-err { color: #f85149; }

/* ── Left sidebar ───────────────────────────────────────── */
#sidebar {
    dock: left;
    width: 26;
    background: #0d1117;
    border-right: solid #1c2333;
    height: 1fr;
}

#sidebar.collapsed {
    width: 0;
    border: none;
    display: none;
}

#sidebar-brand {
    height: 3;
    padding: 1 1 0 1;
    color: #a78bfa;
    text-style: bold;
    border-bottom: solid #1c2333;
}

.sidebar-section {
    color: #6e7681;
    text-style: bold;
    padding: 1 1 0 1;
    height: 2;
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
    background: #1f1635;
    color: #c4b5fd;
    text-style: bold;
    border-left: thick #a78bfa;
}

.sidebar-meta {
    padding: 0 1;
    color: #7d8590;
    height: 1;
}

.sidebar-path {
    padding: 0 1;
    color: #484f58;
    height: 1;
}

#session-list {
    height: 1fr;
    max-height: 14;
    padding-bottom: 0;
}

#btn-new-session {
    margin: 0 1 1 1;
    background: #161b22;
    color: #a78bfa;
    border: tall #30363d;
    text-align: center;
}

#btn-new-session:hover {
    background: #1f1635;
    border: tall #a78bfa;
}

#sidebar-footer {
    height: auto;
    border-top: solid #1c2333;
    padding: 1 0;
}

/* ── Main workspace ─────────────────────────────────────── */
#main-workspace {
    width: 1fr;
    height: 1fr;
    background: #0b0f14;
    layout: vertical;
}

#chat-container {
    width: 1fr;
    height: 1fr;
    background: #0b0f14;
}

#chat-log {
    height: 1fr;
    padding: 1 2;
    scrollbar-background: #0b0f14;
    scrollbar-color: #30363d;
    scrollbar-size: 1 1;
}

.message {
    margin: 0 0 1 0;
    padding: 0 1;
}

.message-user {
    border-left: thick #58a6ff;
    background: #0d1117;
    padding: 1 1;
    margin-bottom: 1;
}

.message-assistant {
    border-left: thick #a78bfa;
    background: #0d1117;
    padding: 1 1;
    margin-bottom: 1;
}

.message-tool {
    border-left: thick #d29922;
    color: #e3b341;
    background: #12100a;
    padding: 0 1;
    margin-bottom: 1;
}

.message-error {
    border-left: thick #f85149;
    color: #ffa198;
    background: #1c0a0a;
    padding: 1 1;
}

.message-system {
    color: #7d8590;
    padding: 0 1;
}

.message-status {
    color: #6e7681;
    text-style: italic;
}

.message-welcome {
    color: #c9d1d9;
    padding: 3 2 2 2;
    text-align: center;
    height: auto;
    width: 100%;
}

/* ── Prompt composer (OpenCode-style) ───────────────────── */
#activity-bar {
    height: 1;
    padding: 0 2;
    background: #0d1117;
    color: #d29922;
}
#composer {

    dock: bottom;
    height: auto;
    min-height: 7;
    max-height: 16;
    background: #0d1117;
    border-top: solid #1c2333;
    padding: 0 1 0 1;
}

#composer-meta {
    height: 1;
    layout: horizontal;
    color: #6e7681;
    padding: 0 1;
}

#composer-agent {
    width: auto;
    color: #a78bfa;
    padding-right: 2;
}

#composer-model {
    width: 1fr;
    color: #58a6ff;
}

#composer-hint {
    width: auto;
    color: #484f58;
    content-align: right middle;
}

#composer-row {
    height: auto;
    layout: horizontal;
}
#btn-send {
    width: 10;
    min-width: 8;
    height: 5;
    margin-left: 1;
    background: #1f1635;
    color: #c4b5fd;
    border: tall #a78bfa;
}
#btn-send:hover {
    background: #2d1f4e;
}
#btn-stop {
    width: 10;
    min-width: 8;
    height: 5;
    margin-left: 1;
    background: #3d1214;
    color: #ffa198;
    border: tall #f85149;
}
#btn-stop:hover {
    background: #5a1d20;
}
#btn-send:disabled {

    opacity: 0.5;
}
#prompt-input {

    height: 5;
    min-height: 4;
    max-height: 12;
    background: #161b22;
    border: tall #30363d;
    padding: 0 1;
    margin: 0 0 0 0;
}

#prompt-input:focus {
    border: tall #a78bfa;
}

#cmd-suggest {
    height: auto;
    max-height: 7;
    background: #161b22;
    border: tall #30363d;
    padding: 0 1;
    display: none;
    margin-bottom: 0;
}

#cmd-suggest.visible {
    display: block;
}

#composer-footer {
    height: 1;
    color: #484f58;
    padding: 0 1;
}

/* ── Status footer ──────────────────────────────────────── */
#footer-bar {
    height: 1;
    background: #010409;
    color: #8b949e;
    text-style: none;

    dock: bottom;
    height: 1;
    background: #010409;
    color: #6e7681;
    padding: 0 1;
    border-top: solid #1c2333;
}

/* ── Dialogs ────────────────────────────────────────────── */
.dialog {
    width: 72;
    max-width: 92%;
    height: auto;
    max-height: 85%;
    background: #161b22;
    border: tall #30363d;
    padding: 1 2;
}

.dialog-title {
    text-style: bold;
    color: #a78bfa;
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

Button {
    background: #21262d;
    color: #e6edf3;
    border: tall #30363d;
}

Button:hover {
    background: #30363d;
}

Button.-primary {
    background: #1f1635;
    color: #c4b5fd;
    border: tall #a78bfa;
}
.tool-card {
    margin: 0 1 1 1;
    padding: 1 2;
    background: #0d1117;
    border: solid #21262d;
    height: auto;
}
.tool-card:hover {
    border: solid #30363d;
}
.tool-card:focus {
    border: solid #a78bfa;
}
.message-user {
    border-left: tall #58a6ff;
}
.message-assistant {
    border-left: tall #a78bfa;
}


#diff-review {
    height: auto;
    max-height: 24;
    margin: 1 1;
    padding: 1;
    background: #0d1117;
    border: solid #30363d;
}
#diff-header {
    height: auto;
    padding-bottom: 1;
}
#diff-body {
    height: 12;
    border: solid #21262d;
}
#diff-actions {
    height: 3;
    padding-top: 1;
}
#diff-footer {
    height: 1;
    color: #6e7681;
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

HEX_BRAND_LINE = "HEX CLI · Powered by HEX · NeonBuild"
