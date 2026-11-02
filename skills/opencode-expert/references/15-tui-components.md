# TUI Components

## Overview

OpenCode surfaces are composed from routes, components, contexts, and UI primitives.
Implementations are source-path-specific; component names in the UI package may change.

## Important component classes

- Conversation/message surfaces.
- Composer/input.
- Header/sidebar/footer/status.
- Tool/result cards.
- Permission/dialog flows.
- Command/session/model dialogs.
- Diff viewer.
- Toasts/loading/error states.

## Component contract

Document purpose, visual structure, interaction, state source, emitted events, and dependencies
before modifying parity.

## HEX implications

HEX widgets are under `hex_cli/tui/widgets/`. Preserve Textual message IDs, reactive state,
keyboard focus, and worker-thread safety.
