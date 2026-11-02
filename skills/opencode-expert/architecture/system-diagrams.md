# OpenCode System Diagrams

## Overall architecture — source verified

```mermaid
flowchart LR
  UI["CLI / TUI / desktop or web"] --> API["Server / protocol API"]
  API --> CORE["Core services"]
  CORE --> AGENT["Agent registry and session runner"]
  CORE --> TOOLS["Tool runtime and registry"]
  CORE --> PERM["Permission service"]
  CORE --> STORE["Session/projector/store"]
  CORE --> PROVIDER["Provider and model services"]
  PROVIDER --> AI["Provider transport adapters"]
  CORE --> MCP["MCP service"]
  CORE --> VCS["Git and snapshot services"]
  CORE --> PLUGINS["Plugins and skills"]
```

## Prompt-to-model flow — partially verified

```mermaid
sequenceDiagram
  participant U as User
  participant S as Session runner
  participant P as Prompt builder
  participant M as Model transport
  participant T as Tool runtime
  U->>S: submit prompt
  S->>P: assemble turn context
  P->>M: invoke selected model
  M-->>S: streamed parts
  alt tool call produced
    S->>T: execute/authorize tool
    T-->>S: tool result
    S->>M: continue turn
  else final response
    S-->>U: publish final message
  end
```

## Streaming flow — partially verified

```mermaid
flowchart LR
  MODEL["Provider stream"] --> TRANSPORT["AI/session transport"]
  TRANSPORT --> EVENTS["LLM event publication"]
  EVENTS --> PROJECTOR["Message/session projector"]
  PROJECTOR --> API["Server event stream"]
  API --> TUI["TUI reactive state"]
```

## Permission approval — source verified

```mermaid
flowchart TD
  REQ["Tool requests permission"] --> RULES{"Match permission rules"}
  RULES -->|allow| RUN["Execute"]
  RULES -->|deny| STOP["Reject"]
  RULES -->|ask| UI["Approval request"]
  UI --> YES["Approved"] --> RUN
  UI --> NO["Denied"] --> STOP
```

## MCP lifecycle — source verified structure

```mermaid
stateDiagram-v2
  [*] --> Configured
  Configured --> Connecting
  Connecting --> Ready: initialize succeeds
  Connecting --> Failed: transport/auth/start fails
  Ready --> Discovering
  Discovering --> Ready: tools/resources/prompts registered
  Ready --> [*]: shutdown
  Failed --> [*]
```

## LSP lifecycle — conceptual only

```mermaid
flowchart TD
  CFG["LSP config and language match"] -.-> START["Start server"]
  START -.-> INIT["Initialize JSON-RPC"]
  INIT -.-> DOCS["Track documents"]
  DOCS -.-> INTEL["Diagnostics/symbols/definitions"]
  INTEL -.-> RECOVER["Restart or report failure"]
```

The dashed path is only a configuration-level finding at the inspected commit; core runtime
ownership was not established.
