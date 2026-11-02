# Security Model

## Overview

Security depends on permission boundaries, external-directory policy, shell execution, credential
handling, configuration trust, MCP connections, plugins, and untrusted tool/model output.

## Trust boundaries

- Project and user configuration.
- Model/tool output.
- Repository files and mentions.
- Child processes and MCP servers.
- Credentials and environment.
- External directories and symlinks.
- Network destinations.

## Required controls

Validate schemas, normalize paths, constrain subprocesses, redact secrets, authorize side
effects, and make failures default-deny.

## HEX implications

Review `permissions.py`, credentials, MCP, filesystem tools, command execution, and Git tools
before feature work. Treat prompt output as untrusted data, never instructions for shell policy.
