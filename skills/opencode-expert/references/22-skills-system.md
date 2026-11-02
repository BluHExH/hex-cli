# Skills System

## Overview

OpenCode has a core skill service and discovery/loading modules:

- `packages/core/src/skill.ts`
- `packages/core/src/skill/discovery.ts`
- `packages/core/src/session/skill.ts`
- server handler and API protocol paths.

## Format and discovery

Official skills documentation uses skill folders with instructions in Markdown. The portable
skill mechanism should require stable metadata, scoped discovery, bounded references, and safe
instruction injection.

## Invocation

Skills may be discovered on demand or selected from session context. Loading instructions must
be attributable and not silently elevate permissions.

## HEX implications

HEX `hex_cli/skills/loader.py` discovers project/global `SKILL.md`. Production agent-loop
injection is not verified; first add provenance, caching, scope, and prompt tests.
