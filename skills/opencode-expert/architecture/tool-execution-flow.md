# Tool Execution Flow

```mermaid
sequenceDiagram
  participant Runner as Session runner
  participant Model as Model/provider
  participant Registry as Tool registry
  participant Policy as Permission
  participant Exec as Tool implementation
  Runner->>Model: send prompt/model parts
  Model-->>Runner: tool-call request
  Runner->>Registry: resolve tool and schema
  Registry->>Policy: enforce permission rule
  alt allowed
    Policy-->>Exec: authorized
    Exec-->>Runner: structured result
    Runner-->>Model: continue with result
  else denied
    Policy-->>Runner: denial/error
  else requires approval
    Policy-->>Runner: approval request
  end
```

The diagram describes verified architectural responsibilities. Validate current schemas and
result semantics against `packages/core/src/tool.ts`, `packages/core/src/tool/runtime.ts`,
and `packages/core/src/tool/plugin/**`.
