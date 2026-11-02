---
name: opencode-expert
description: "Technical research and implementation reference for understanding OpenCode architecture and applying verified concepts to HEX CLI"
---

# OpenCode Expert Skill

## Purpose

OpenCode Expert is a source-grounded knowledge base for HEX CLI engineering. It explains
OpenCode's architecture and behavior at a versioned level, and turns those findings into
native, compatible implementation guidance for HEX CLI.

OpenCode is a technical reference, not HEX CLI's identity. HEX CLI remains HEX / NeonBuild:
retain its Python + Textual implementation, branding, commands, configuration compatibility,
and user-facing behavior.

Use this Skill for OpenCode-inspired features, TUI work, agent runtime changes, session
management, tools, permissions, context, providers, MCP/LSP, configuration, commands,
diffs, reliability, security, and feature-parity analysis.

## Mandatory workflow

1. Identify the requested feature and uncertainty.
2. Read the relevant references from this skill.
3. Verify changing behavior in the current official documentation.
4. Inspect actual OpenCode source where implementation details matter.
5. Inspect the corresponding HEX CLI implementation and tests.
6. Compare runtime boundaries, state ownership, and compatibility.
7. Write a native implementation plan with regression and security risks.
8. Implement without copying OpenCode source or replacing HEX architecture.
9. Run focused tests, then the full applicable regression suite.
10. Update the parity matrix and relevant references with verified findings.

## Accuracy and evidence policy

- Never invent an OpenCode feature, API, file, function, event, or behavior.
- Facts must be tied to current documentation, official release metadata, or inspected
  source paths in the pinned source version.
- Distinguish `DOCUMENTED`, `SOURCE VERIFIED`, `PARTIAL`, and `UNVERIFIED`.
- Treat documentation/source disagreements as unresolved until tested.
- Do not infer HEX implementation merely from similarly named modules.
- Do not copy source wholesale. Use links, summaries, diagrams, and small original examples.
- Keep per-module limitations explicit.

## Reference navigation

- [Overview](references/01-opencode-overview.md)
- [Architecture](references/02-system-architecture.md)
- [Agent runtime](references/03-agent-runtime.md)
- [Agent types](references/04-agent-types.md)
- [Subagents](references/05-subagent-system.md)
- [Tools](references/06-tool-system.md)
- [Permissions](references/07-permission-system.md)
- [Sessions](references/08-session-management.md)
- [Storage](references/09-session-storage.md)
- [Streaming](references/10-streaming-engine.md)
- [Context](references/11-context-management.md)
- [Providers](references/12-provider-system.md)
- [Models](references/13-model-management.md)
- [TUI architecture](references/14-tui-architecture.md)
- [TUI components](references/15-tui-components.md)
- [Shortcuts](references/16-keyboard-shortcuts.md)
- [Commands](references/17-command-system.md)
- [Diffs and snapshots](references/18-diff-snapshot-system.md)
- [MCP](references/19-mcp-integration.md)
- [LSP](references/20-lsp-integration.md)
- [Plugins](references/21-plugin-system.md)
- [Skills](references/22-skills-system.md)
- [Configuration](references/23-configuration.md)
- [Server API](references/24-server-api.md)
- [Git](references/25-git-integration.md)
- [Errors](references/26-error-handling.md)
- [Security](references/27-security-model.md)
- [Testing](references/28-testing-strategy.md)

## Architecture and mapping

- [System diagrams](architecture/system-diagrams.md)
- [Agent lifecycle](architecture/agent-lifecycle.md)
- [Tool execution flow](architecture/tool-execution-flow.md)
- [Session lifecycle](architecture/session-lifecycle.md)
- [TUI rendering flow](architecture/tui-rendering-flow.md)
- [HEX architecture](hex-mapping/hex-architecture.md)
- [Feature parity matrix](hex-mapping/feature-parity-matrix.md)
- [Implementation roadmap](hex-mapping/implementation-roadmap.md)
- [Compatibility guide](hex-mapping/compatibility-guide.md)

## Source grounding

- [Official documentation index](sources/official-documentation.md)
- [OpenCode source map](sources/source-code-map.md)
- [Source manifest](sources/source-manifest.json)
- [Version history](sources/version-history.md)

## Quick glossary

- **Primary agent**: An agent that owns a user-facing session turn.
- **Subagent**: A delegated child agent invocation, not automatically a separate process.
- **Session projector**: A representation derived from persisted messages/events.
- **Tool boundary**: The code boundary that validates, authorizes, executes, and records a tool.
- **Snapshot**: A recovery point for files; separate from ordinary Git commits or branches.
- **Streaming frame**: A model or runtime event that updates the client incrementally.
