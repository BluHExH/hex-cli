# Server API

## Overview

Typed server protocol groups are under `packages/protocol/src/groups/**`, while handlers are in
`packages/server/src/handlers/**`.

## Verified patterns

- Session, command, config, MCP, skill, and VCS handler groups.
- Shared protocol routes consumed by clients.
- Server event streams must be audited per exact route and version.

## Error responses

Prefer typed protocol errors over string matching. Preserve request identity, session identity,
and safe redaction.

## HEX implications

HEX has no equivalent durable server API or HTTP event service. Do not implement parity solely
because core services share concepts; define requirements and native Python API boundaries.
