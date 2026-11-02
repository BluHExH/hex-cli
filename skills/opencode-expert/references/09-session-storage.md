# Session Storage

## Overview

`packages/core/src/session/store.ts`, `sql.ts`, `message.ts`, and projector/history modules
separate persistence, projections, and runtime handles. Message schemas are under
`packages/schema/src/session-message.ts`.

## Persistence concerns

- Session identity and parent relationships.
- Message ownership and ordering.
- Runtime-only state versus durable state.
- Transactions and recovery.
- Migration/schema evolution.
- History indexing and integrity.

## Status

SQL/session storage behavior is source verified structurally, but exact backend, migrations,
transaction boundaries, and retention should be pinned to the inspected schema and SQL files.

## HEX implications

HEX persists sessions as JSON under `~/.hex/sessions`. Writes are atomic. Messages remain
verbatim; only metadata has secret stripping. Adding versioned migrations and storage integrity
tests is more compatible than replacing JSON with SQLite.
