# TUI Rendering Flow

## Conceptual OpenCode flow

```mermaid
flowchart LR
  INPUT["Terminal input"] --> EVENT["TUI event"]
  EVENT --> CONTEXT["TUI contexts/state"]
  CONTEXT --> MODEL["Reactive UI model"]
  MODEL --> COMPONENT["Route/component render"]
  COMPONENT --> SCREEN["Terminal output"]
  API["Server event stream"] --> CONTEXT
```

The concrete implementation is split among `packages/tui/src/app.tsx`, contexts, routes, and
components at commit `ff90ed91607cabf420a369e9009539c1aa0932af`.

## HEX flow — source inspected

```mermaid
flowchart LR
  KEYS["Textual messages/key events"] --> APP["HexApp"]
  APP --> STATE["SessionState/UI state"]
  STATE --> WIDGETS["Textual widgets"]
  WORKER["Agent worker thread"] --> HOOK["UI hooks/callbacks"]
  HOOK --> STATE
  WIDGETS --> SCREEN["Terminal output"]
```
