# MCP Integration

## Overview

OpenCode's MCP service is under `packages/core/src/mcp/**`, with server handlers and protocol
definitions.

## Lifecycle

- Load server configuration.
- Start/transport-connect.
- Authenticate where applicable.
- Initialize protocol.
- Discover tools/resources/prompts.
- Register tools in tool runtime.
- Handle calls/errors/reconnects.
- Disconnect and clean up.

## Source areas

`packages/core/src/mcp/index.ts`, `connection.ts`, `client.ts`, `stdio.ts`,
`socket-client.ts`, `oauth.ts`, and server/protocol handlers.

## HEX implications

`hex_cli/mcp/client.py` has stdio sessions and tool listing/calling, but HTTP servers and
model-loop integration are missing. Start with process lifecycle, credentials, timeout, tool
schema conversion, and permission tests.
