# OpenCode Source Code Map

Pinned revision: `ff90ed91607cabf420a369e9009539c1aa0932af`; inspected 2026-11-02.

| System | Source area |
|---|---|
| Agents | `packages/core/src/agent.ts`, `packages/core/src/session/runner/**` |
| Session/message storage | `packages/core/src/session.ts`, `packages/core/src/session/**`, `packages/schema/src/session-message.ts` |
| Tools | `packages/core/src/tool.ts`, `packages/core/src/tool/**` |
| Permissions | `packages/core/src/permission.ts`, `packages/core/src/permission/**` |
| Providers/models | `packages/core/src/provider.ts`, `packages/core/src/model.ts`, `packages/core/src/model-resolver.ts`, `packages/ai/src/**` |
| TUI | `packages/tui/src/**` |
| Server/protocol | `packages/server/src/**`, `packages/protocol/src/**`, `packages/httpapi-codegen/**` |
| MCP | `packages/core/src/mcp/**`, `packages/server/src/handlers/mcp.ts` |
| LSP | `packages/schema/src/config/lsp.ts`; runtime implementation not confirmed in core snapshot |
| Plugins | `packages/core/src/plugin.ts`, `packages/core/src/plugin/**`, `packages/plugin/**` |
| Skills | `packages/core/src/skill.ts`, `packages/core/src/skill/**` |
| Commands/config | `packages/core/src/command.ts`, `packages/core/src/config.ts`, `packages/core/src/config/**` |
| Snapshots/diff | `packages/core/src/snapshot.ts`, `packages/core/src/session/diff.ts`, `packages/core/src/git.ts` |
| Git/VCS | `packages/core/src/git.ts`, `packages/core/src/vcs.ts`, `packages/core/src/vcs/**` |
| Tests | `packages/core/test/**`, `packages/server/test/**`, `packages/tui/test/**`, `packages/cli/test/**`, `packages/ai/test/**` |

Use the GitHub tree links in the manifest when line-specific URLs are required. Source moves
between commits; path evidence should be refreshed with the source manifest.
