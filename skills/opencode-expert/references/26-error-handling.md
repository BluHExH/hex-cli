# Error Handling

## Overview

Errors can occur in provider auth/transport, model output, tool validation/execution, session
persistence, permission UI, MCP/LSP processes, plugins, and terminal rendering.

## Required design

- Typed error category and stable code.
- User-visible safe message and redacted details.
- Cause/operation context.
- Retryability/cancellation indicator.
- Recovery action.
- Structured logging with secret filtering.

## OpenCode source areas

Follow provider/AI and tool/session implementations, service boundaries, server handlers, and
TUI error presentation; exact taxonomy is version-specific.

## HEX implications

Standardize loop exceptions and provider/tool failures in Python. Ensure cancellation leaves
tools, workers, subprocesses, and session state in observable terminal states.
