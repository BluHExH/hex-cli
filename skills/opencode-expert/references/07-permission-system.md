# Permission System

## Overview

OpenCode defines allow, deny, and ask rules in the core permission service:
`packages/core/src/permission.ts` and `packages/core/src/permission/saved.ts`.

## Rules and approval

A permission match should produce one explicit outcome. Ask implies UI approval, timeout/failure
must default safely, and persistent decisions require a stable scope.

## Security boundaries

Treat shell commands, writes, external paths, credentials, Git pushes, deployments, MCP servers,
and plugins as distinct or configurable permission domains.

## HEX implications

`hex_cli/permissions.py` implements modes, high-impact command detection, path containment, and
blocking fragments. The TUI approval bridge waits for a dialog result from the worker.

## Known risks

- Thread blocking.
- Ambiguous rule precedence.
- Persisted decisions becoming broader than intended.
- Paths escaping containment through symlinks or normalization.

## Recommended tests

Use filesystem traversal, shell chaining, symlinks, external directories, timeout, denial,
allow persistence, and concurrent approval cases.
