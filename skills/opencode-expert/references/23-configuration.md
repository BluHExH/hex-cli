# Configuration

## Overview

OpenCode configuration spans core config discovery, normalization, watching, environment,
providers, agents, tools, permissions, MCP/LSP, and integrations.

## Verified source areas

- `packages/core/src/config.ts`
- `packages/core/src/config/**`
- schema packages under `packages/schema/src/config/**`
- server and command handlers.

## Precedence

Document global/project/environment precedence only after inspecting normalize and discovery.
Schema validation should produce safe user-facing errors and preserve unknown configuration
where forward compatibility permits.

## HEX implications

HEX global/project JSON config is in `hex_cli/config.py`; project overrides tighten permissions.
Keep credentials separate and test dotenv/global/project precedence.
