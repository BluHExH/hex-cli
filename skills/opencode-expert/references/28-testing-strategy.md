# Testing Strategy

## Overview

OpenCode tests are organized by package under core, server, TUI, CLI, AI, app/browser, and plugin
areas in the inspected repository.

## Test patterns to look for

- Unit services and typed state transitions.
- Mock provider/model streams.
- Tool schemas, validation, execution, and errors.
- Permission allow/deny/ask decisions.
- Session persistence/projectors.
- MCP process and protocol integration.
- TUI rendering and interactions.
- Platform/process compatibility.

## HEX implications

HEX baseline has pytest coverage for agent, tools, providers, permissions, sessions, diff review,
TUI layout, MCP schema behavior, commands, skills, and subagents. Add contract tests for missing
integrations before UI features.
