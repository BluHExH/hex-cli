# System Architecture

## Overview

OpenCode separates interactive surfaces from core services and a protocol/server boundary.
The inspected source contains CLI/TUI entry packages, core runtime services, protocol and
generated HTTP definitions, provider adapters, and application surfaces.

## Runtime boundaries

- `packages/cli` launches terminal or other UI entry points.
- `packages/tui` owns terminal rendering and UI contexts/components.
- `packages/core` owns domain services, sessions, tools, permissions, agents, and providers.
- `packages/server` exposes protocol handlers.
- `packages/protocol` defines typed API groups.
- `packages/ai` owns provider/model transport primitives.

## Data flow

UI input enters the session runner; the runner builds prompts, invokes models, publishes
stream parts, executes authorized tools, and projects results into session state. Server and
TUI consumers read this state or its events.

## State ownership

Session messages, runtime handles, tools, permissions, provider/model registries, MCP
connections, plugins, and configuration are distinct service lifecycles. Avoid coupling UI
state directly to provider internals.

## Source references

- `packages/core/src/session/runner/index.ts`
- `packages/core/src/agent.ts`
- `packages/core/src/tool.ts`
- `packages/protocol/src/api.ts`
- `packages/server/src/routes.ts`

## HEX implications

HEX's `HexApp`, `AgentLoop`, registry classes, JSON session store, and provider tools already
express similar boundaries in Python; retain native boundaries.
