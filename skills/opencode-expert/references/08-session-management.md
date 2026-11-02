# Session Management

## Overview

Core session APIs are represented by `packages/core/src/session.ts` and
`packages/core/src/session/session.ts`.

## Lifecycle concepts

- Create/restore session handle.
- Own messages and child sessions.
- Continue parent-child work.
- Switch/resume a session.
- Search/title/export where supported.
- Fork/revert/delete.
- Persist terminal output and runtime state according to policy.

## Source-grounded data

Session, message, history, projector, and SQL modules exist separately under
`packages/core/src/session/**`. This suggests projected runtime views are derived from more
fundamental stored state.

## HEX implications

HEX has durable session JSON and runtime state separated in `SessionStore` and `tui/state.py`.
Session switching, search, title, export, load, and deletion must avoid cross-session worker
state.

## Known limitations

Fork, archive, and parent-child semantics require pinned source inspection before describing
exact APIs.
