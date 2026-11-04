# Changelog

## 2.2.0 — OpenCode v2 TUI reskin

- Rebuilt TUI to mirror the real OpenCode v2 terminal UI (single-column, OpenCode black/blue palette):
  - Session header `# title` with live tokens · context % · cost stats
  - User messages as blue-left-bar blocks; assistant replies as plain text
  - Tool lines in OpenCode style: `* Glob "src" (2 entries)`, `* Write "…" (46 chars)`, errors as `! …`
  - Composer block with `Build · model · HEX` row; Tab cycles **Build ⇄ Plan** (Plan denies writes/shell via gate wrapper)
  - Hint line: `· dots ·  esc interrupt ·  tab agents  ctrl+p commands  ctrl+n new session`
- Slash commands mirroring OpenCode TUI docs: `/new /clear /sessions /models /undo /compact /summarize /details /help /exit` (+ aliases `/resume /continue /q`)
  - Type-ahead hint popup above the composer while typing `/`
- Ctrl+P searchable command dialog; Sessions dialog; Models dialog
- `!` prefix runs shell commands through the tool pipeline; result recorded to history
- `/undo` removes the last exchange; `/compact` runs real context compaction; `/details` toggles tool lines (replay-based)
- `ChatMessage.meta` carries tool args so replay renders exact tool lines
- Old three-column rails removed; screenshots regenerated for the new layout

## 2.1.3 — Reference fidelity hardening

- Header renders real git state: branch chip `⎇ <branch> <count>` bound to the app workspace (cwd fix)
- Fixed top header + status bar never rendering (border-box left zero content rows)
- Real per-tool durations in tool cards and Tools Activity (monotonic timing in runner)
- Mock provider multi-turn fix: summarize only after the tool result of the current exchange
- Windows-safe 12h clocks (`%I:%M %p`), one-decimal context meter, composer toolbar chips, violet context bar
- New bindings: Ctrl+K palette, Ctrl+Enter submit
- Regenerated reference SVGs incl. changes rail with real `+delta` rows
- Capture script spins a real git repo for genuine header data

## 2.1.2 — Reference workspace visual match

- Tighten three-column proportions, header/status, tool cards, composer toolbar
- Left/right rails section order aligned to reference image
- Visual match report + Textual grid screenshots

# Changelog

## 2.1.1 — Three-column workspace TUI

- Left / center / right layout matching professional coding-agent structure
- Tool execution cards, changes & activity rails, context meter
- Composer toolbar + Enter submit
- SVG screenshots under docs/screenshots/

# Changelog

## 2.1.0 — TUI/UX redesign

- Professional layout: header, sidebar, home, timeline, composer, status
- Design tokens theme system
- Command palette (Ctrl+P)
- Responsive sidebar
- Multiline composer (Ctrl+Enter)
- Backend unchanged from 2.0.1

## 2.0.1 — Release stabilization

- Fix console entry point: `hex_cli.main:main`
- Align package/runtime version to **2.0.1**
- Rewrite README for actual 2.0 architecture
- Shell: default `shell=False` argv execution; explicit `use_shell`; cancel/timeout
- Cooperative agent cancellation + shell process terminate
- TUI: threaded workers; Ctrl+C cancels in-flight turn
- Textual moved to optional `[tui]` / `[dev]` extra
- Version consistency regression test

## 2.0.0 — Clean architecture rebuild

- Modular agent, providers, tools, permissions, sessions, changes, TUI core
