# Git Integration

## Overview

OpenCode core has Git execution/repository abstractions and VCS snapshot support in
`packages/core/src/git.ts` and `packages/core/src/vcs/**`.

## Behaviors

- Repository detection/status/branch.
- Diff generation and patch application.
- Worktree awareness where supported.
- Commit/push boundaries.
- Snapshot interaction separate from Git history.

## Security

Git operations can delete or publish data. Confirm repository/worktree and user intent, and
route destructive/publishing operations through permissions.

## HEX implications

HEX exposes GitTools and worktree management. Preserve explicit approvals and native GitPython
error handling.
