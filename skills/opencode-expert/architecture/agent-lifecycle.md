# Agent Lifecycle

## Verified structure

The core contains an agent registry (`packages/core/src/agent.ts`) and a session runner
organized as drain, prompt, LLM, and step modules:

- `packages/core/src/session/runner/index.ts`
- `packages/core/src/session/runner/prompt.ts`
- `packages/core/src/session/runner/llm.ts`
- `packages/core/src/session/runner/step.ts`
- `packages/core/src/session/runner/publish-llm-event.ts`

```mermaid
stateDiagram-v2
  [*] --> Queued
  Queued --> PreparingPrompt
  PreparingPrompt --> InvokingModel
  InvokingModel --> Streaming: model emits parts
  Streaming --> InvokingModel: more model parts
  InvokingModel --> ExecutingTools: tool calls
  ExecutingTools --> InvokingModel: results added and turn continues
  InvokingModel --> Finalizing
  ExecutingTools --> Cancelled: cancellation
  InvokingModel --> Failed: provider/runtime error
  Finalizing --> Complete
  Complete --> [*]
  Failed --> [*]
  Cancelled --> [*]
```

Exact provider-retry and continuation rules must be rechecked in `llm.ts` and provider
adapters for each implementation version.
