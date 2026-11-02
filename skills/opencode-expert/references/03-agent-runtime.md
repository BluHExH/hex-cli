# Agent Runtime

## Overview

The OpenCode core has a session runner that drains queued work and coordinates prompt,
model, streaming, tool, and continuation phases.

## Verified modules

- `packages/core/src/session/runner/index.ts`: runner service and drain result.
- `prompt.ts`: prompt construction.
- `llm.ts`: model invocation and continuation.
- `step.ts`: one step outcome.
- `publish-llm-event.ts`: publishes model/session events.

## Execution flow

1. Open or continue a session turn.
2. Assemble prompt and runtime context.
3. Invoke selected model and stream parts.
4. Resolve tool calls.
5. Apply permission policy.
6. Execute authorized tools and append results.
7. Continue or finalize.

## Lifecycle

Cancellation, provider failure, tool failure, and terminal output require separate branches.
Do not equate transport cancellation with session deletion.

## Tests

Look for runner, LLM, step, session, and provider behavior under `packages/core/test/**`.

## HEX implications

HEX's `AgentLoop.run` is bounded and supports provider response/tool loops and cooperative
cancellation in `hex_cli/agent/loop.py`. Native improvements should normalize partial outputs,
typed failures, and tool continuation before expanding parallelism.
