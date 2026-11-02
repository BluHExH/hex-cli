# Command System

## Overview

OpenCode core has command metadata/handlers in `packages/core/src/command.ts`, with server and
TUI integrations.

## User-facing behavior

Built-in slash commands, custom commands, arguments, discovery, command palette access, and
execution are separate concerns. Custom templates must define variable expansion and reserved
names safely.

## HEX implications

HEX custom commands are Markdown templates loaded by `hex_cli/commands_ext/loader.py`, rendered
and dispatched by the TUI. Supported variables include arguments and template interpolation as
implemented by the loader.

## Security

Treat template bodies and arguments as untrusted prompt text. Do not interpret template text as
shell commands without explicit restrictions.
