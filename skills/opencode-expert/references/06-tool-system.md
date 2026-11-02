# Tool System

## Overview

Tools join model-generated calls to typed runtime operations. Core code defines the registry,
registration rules, conversion to provider formats, and execution in `tool.ts` and
`tool/runtime.ts`.

## Built-in tool families

The source tree under `packages/core/src/tool/**` contains implementation families rather than
one guaranteed list. Enumerate files in the pinned commit before claiming names.

## Lifecycle

1. Register tool metadata and provider schema.
2. Model emits a tool call.
3. Validate arguments.
4. Check permission policy.
5. Execute with timeout/context boundaries.
6. Convert output.
7. Handle error/partial/cancellation.
8. Publish result into the session and continue.

## Custom and MCP tools

Custom tools and MCP registrations should enter through a common schema and permission adapter.
Names/IDs must avoid collisions and prompt injection should not bypass validation.

## HEX implications

HEX has filesystem, shell, project, and Git tools in `hex_cli/tools/*.py`, with central schemas
in `registry.py`. Add MCP registration through the same runtime boundary rather than special
case dispatch.
