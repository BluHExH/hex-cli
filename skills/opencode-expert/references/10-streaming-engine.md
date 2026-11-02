# Streaming Engine

## Overview

OpenCode's AI package streams provider output and core session modules translate model frames
into session events.

## Verified source areas

- `packages/ai/src/llm.ts`
- `packages/ai/src/effect.ts`
- `packages/core/src/session/model-transport.ts`
- `packages/core/src/session/runner/publish-llm-event.ts`

## Event flow

Provider chunks become normalized model parts/events. The session runner publishes updates,
projectors update message state, server/TUI subscribers observe progress, tool events appear
between model parts, and finalization publishes terminal state.

## Failure handling

Separate transport EOF, provider error, tool-call error, user cancellation, and malformed stream
events. Partial output must be preserved or marked reliably, never silently finalized.

## HEX implications

HEX has a `StreamEngine` normalized parser, provider hooks, and Textual streaming updates. The
provider base currently mixes response and stream contracts; complete and test stream
termination, chunk accounting, tool-call chunks, and cancellation.
