# Agent Types

## Overview

OpenCode has named agents selected for builds, questions, planning, and custom workflows.
The service is defined in `packages/core/src/agent.ts`.

## Configuration dimensions

Official concepts include primary agents, modes, custom agent definitions, selected models,
tool permissions, and agent-specific prompts. Exact fields and defaults vary by version; use
the source schema/config package when implementing.

## Switching behavior

User-facing switching must update prompt policy and tool authorization together. Changing only
a label without changing execution policy creates misleading behavior.

## HEX mapping

`hex_cli/agent/loop.py` currently supports loop profiles such as build and plan/review-style
behavior and constrains tool access. It should evolve toward a validated agent registry rather
than UI-only profile names.

## Known limitations

Do not claim exact built-in agent names, modes, or inheritance semantics without inspecting
the current `Agent.Service` and configuration schemas.
