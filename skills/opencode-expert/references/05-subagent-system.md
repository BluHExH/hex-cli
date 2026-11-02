# Subagent System

## Overview

A subagent is a delegated child invocation owned by a parent turn. It may share runtime
services without being a separate OS process.

## Source evidence

Official/core task-oriented paths and `packages/core/src/agent.ts` establish delegated agent
support. Exact child-session mechanics should be verified at the current commit.

## Required lifecycle

- Delegation request and bounded task.
- Parent-child relationship and task context.
- Independent resource/change limits.
- Structured result propagation.
- Cancellation and failure handling.
- Cleanup and parent continuation.

## Parallel execution

Parallelism is an execution policy, not proof of isolation. Shared files and credentials can
remain coupled even when calls execute on separate workers.

## HEX implications

`hex_cli/subagents/runtime.py` provides real thread-backed child loops and limits. It is
library-level and not observed on production call paths. Wire it through tools/commands only
after adding session isolation, cancellation, and merged-change review.
