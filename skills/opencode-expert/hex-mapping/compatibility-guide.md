# HEX/OpenCode Compatibility Guide

## Do not adopt blindly

HEX CLI is Python and Textual. Do not port TypeScript package boundaries, names, or UI APIs
unless a native concept has clear product value.

## Preserve

- HEX / NeonBuild branding and text.
- Existing CLI flags and custom slash-command behavior.
- Session JSON compatibility and atomic writes.
- Provider configuration and credential storage compatibility.
- Existing permission modes unless migration is explicit.
- TUI keyboard behavior unless conflicts are resolved.

## Adapt

| OpenCode Concept | HEX Native Form |
|---|---|
| Effect/session services | Python classes/services behind existing modules |
| Protocol schemas | Typed dataclasses/Pydantic models |
| Bun/JS plugins | Python modules or entry points |
| Solid/JSX TUI | Textual widgets and reactive state |
| SQLite session store | Preserve JSON compatibility; migrate intentionally |
| MCP SDK internals | Existing async stdio JSON-RPC adapter |
| Server event streams | Textual callbacks or native async event queues |

## Migration rules

- Version any new persisted config.
- Default to backward-compatible behavior.
- Reject ambiguous or untrusted configuration.
- Keep destructive operations opt-in and approved.
- Add test fixtures for old config/session formats.
