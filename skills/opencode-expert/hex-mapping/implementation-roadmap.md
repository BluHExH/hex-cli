# HEX CLI Implementation Roadmap

Prioritize native reliability before feature breadth.

## 1. Runtime correctness

- Normalize provider/tool/error/cancellation result types.
- Make stream adapter failures observable and terminal.
- Add bounded retries only where provider identity permits.

## 2. Session and state isolation

- Preserve JSON atomic writes.
- Define fork/resume ownership and prevent worker state crossing sessions.
- Add schema version and corruption recovery tests.

## 3. Tool execution reliability

- Centralize validation, authorization, execution, timeout, and structured output.
- Merge MCP tools through an adapter only after loop integration is complete.

## 4. Permission and security

- Standardize rule precedence, persist only explicit decisions, and keep approval UI responsive.
- Expand symlink/external-directory checks and command policy.

## 5. Context and streaming

- Implement a model-context budget contract.
- Complete normalized provider streaming and cancellation.
- Add compaction only with loss review and provenance.

## 6. TUI interaction and polish

- Focus on active-session isolation, keyboard help, diff review, loading/error states, and resize.

## 7. MCP/LSP

- MCP stdio end-to-end first; remote HTTP separately.
- Add LSP lifecycle, document synchronization, diagnostics, and hover/symbol queries.

## 8. Advanced agent capabilities

- Wire subagents, skills, and richer profiles only after session/tool isolation is tested.
