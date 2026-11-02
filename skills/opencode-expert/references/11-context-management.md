# Context Management

## Overview

Context consists of system/agent instructions, conversation history, file context, tool output,
and provider-specific limits. Exact compaction is version-sensitive.

## Principles

- Count based on provider/model configuration.
- Preserve recent user intent and active file/project context.
- Track compacted summaries separately from raw history.
- Bound tool output before it enters model history.
- Make pruning/removal deterministic and observable.

## Source evidence status

Relevant session, prompt, and history modules exist, but the inspected pass did not verify a
single universal algorithm. Do not document provider-dependent compaction without source.

## HEX implications

HEX constructs history in the agent loop and should add model-aware budgets, bounded tool
output, and explicit recoverable summaries. Persist raw/session history separately from the
model context sent to providers.
