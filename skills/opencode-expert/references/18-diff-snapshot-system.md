# Diff and Snapshot System

## Overview

OpenCode has snapshot and diff services in the core:

- `packages/core/src/snapshot.ts`
- `packages/core/src/session/diff.ts`
- `packages/core/src/git.ts`

## Behaviors

Record file recovery points, detect changes, generate diffs, support undo/restore, and isolate
changes by session/turn. External modifications and Git state require conflict handling.

## Snapshot versus Git

A snapshot can restore pre-session file content without creating commits. Git status/diffs and
commits are repository operations with separate semantics.

## HEX implications

`hex_cli/changes/tracker.py` records content diffs, line statistics, undo/redo, and restoration.
It is runtime/session-memory based and deletion redo remains limited. Persist snapshots only
with explicit format/version and recovery tests.
