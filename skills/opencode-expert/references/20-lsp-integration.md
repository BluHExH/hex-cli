# LSP Integration

## Overview

The pinned OpenCode source verifies an LSP configuration schema, not a complete core runtime
path: `packages/schema/src/config/lsp.ts`. App/settings UI references also exist.

## User capabilities expected from language servers

- Diagnostics.
- Definitions/references.
- Hover.
- Document/symbol queries.
- Language detection and document synchronization.
- Restart/recovery.

## Status

Runtime lifecycle is `PARTIAL/UNVERIFIED` for this snapshot. Do not claim core ownership until
process, transport, and request paths are inspected in the target commit.

## HEX implications

`hex_cli/lsp/client.py` has JSON-RPC initialization and document queries. Wire lifecycle and
incremental document updates before exposing user features.
