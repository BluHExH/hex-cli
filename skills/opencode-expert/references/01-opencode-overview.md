# OpenCode Overview

## Overview

OpenCode is an open-source AI coding agent available as a terminal interface, desktop app,
and IDE extension. Official documentation frames provider configuration, project
initialization, prompting, plan mode, file changes, undo, redo, and customization as its
central user workflow.

**Evidence:** official documentation landing page; repo commit inspected 2026-11-02.

## Major subsystems

- CLI/TUI and optional app surfaces.
- Agent and session runtime.
- Tool and permission services.
- Provider/model abstraction and streaming.
- MCP, LSP/configuration, plugins, and skills.
- Git/VCS, snapshots/diffs, and server API.

## Project structure

The pinned source snapshot contains packages for `core`, `ai`, `schema`, `protocol`, `server`,
`tui`, `cli`, SDK/client output, app/desktop surfaces, plugins, and shared utilities.

## HEX implications

Do not treat surface availability as architectural parity. HEX is a Python/Textual CLI and
should implement equivalent behavioral capabilities native to that product.

## Limitations

Versioned packaging differs between OpenCode V1 and V2 documentation. Verify commands and
internal APIs with the pinned commit before implementation.
