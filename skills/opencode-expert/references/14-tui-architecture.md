# TUI Architecture

## Overview

The inspected OpenCode terminal UI is under `packages/tui/src`; it includes app composition,
routes/components, contexts, plugins, and shared UI code.

## Lifecycle

- Terminal startup and capability detection.
- Build app/context providers.
- Mount route/screen composition.
- Receive terminal and server/API events.
- Update reactive state.
- Render output and handle resize/focus.

## Source areas

- `packages/tui/src/index.tsx`
- `packages/tui/src/app.tsx`
- `packages/tui/src/routes/**`
- `packages/tui/src/component/**`
- `packages/tui/src/context/**`
- `packages/tui/src/ui/**`

## HEX implications

HEX uses Textual and Python. Preserve native widget/message architecture, worker thread UI
callbacks, CSS/layout behavior, and focus semantics.
