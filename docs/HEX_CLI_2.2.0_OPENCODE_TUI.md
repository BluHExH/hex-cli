# HEX CLI 2.2.0 — OpenCode v2 TUI Reskin

The HEX CLI terminal UI was rebuilt to mirror the **real OpenCode v2 TUI**
(sst/opencode screenshot: lander/screenshot.png, TUI docs commands) instead of the
earlier three-column reference-image interpretation. HEX branding retained; OpenCode is
the structural reference.

## Layout (matches the official screenshot)
- **Session header**: `# <session title>` bold left; right side live stats
  `<tokens> <ctx%> ($<cost>)` — computed from real history (`chars/4` tokens, % of
  `context_max_chars`), `$0.00` for the mock provider.
- **Conversation**: user messages render as blocks with a blue left bar `▌` and subtle
  background; assistant replies are plain text; tool calls are grey OpenCode-style lines
  with derived summaries from real output:
  - `* Glob "src" (2 entries)`, `* Grep "pattern" (N matches)`, `* Read "…"`,
    `* Write "…" (46 chars)`, `* Bash "!cmd"` (+ first 3 output lines)
  - failed tools: `! Tool "arg" <error>`
- **Composer**: blue-left bordered block; bottom row `Build  mock-smart  HEX`
  (agent mode in accent blue, model bold, brand muted). Empty input shows just the block
  cursor.
- **Status line**: `· · · · · ·  esc interrupt   tab agents  ctrl+p commands  ctrl+n new session`.

## Agent modes (Tab)
- **Build** — full access, gate comes from `permission_mode`.
- **Plan** — read-only: a `_PlanGate` wrapper denies `write`/`shell` actions while
  allowing read/list/search, mirroring OpenCode's plan agent.

## Commands (per OpenCode TUI docs)
- Slash: `/new` `/clear` `/sessions` `/resume` `/continue` `/models` `/undo` `/compact`
  `/summarize` `/details` `/help` `/exit` `/quit` `/q`
- Typing `/` opens a hint popup above the composer (prefix-filtered, up to 6 rows).
- `ctrl+p` / `/help` open the searchable command dialog.
- Dialogs: Sessions (pick, reload + replay), Models (configured providers marked).
- Keybinds: `tab` agents · `ctrl+n` new · `ctrl+s` sessions · `ctrl+m` models ·
  `ctrl+u` undo · `ctrl+p` commands · `esc` interrupt.
- `!` prefix: runs a shell command through the real tool pipeline, shows
  `* Bash "…"` lines, records user+tool+assistant messages to history so `/undo` works.

## Session semantics
- `/undo` drops the last user message and everything after it, then replays the
  timeline from `history` (tool metadata kept in `ChatMessage.meta`).
- `/details` toggles tool lines by replaying the history.
- `/compact` runs `context.compact_messages` at quarter budget and replays.
- Session titles adopt the first user message (OpenCode behavior).

## Removed
- Left/right rails, welcome banner, tool cards — replaced by the single-column layout.

## Verification
- `pytest`: 23 passed (layout, header stats, turn rendering, unknown-command note,
  undo semantics, plan-mode denials, dialog dismiss).
- Screenshots regenerated: `docs/screenshots/ref_match_*.svg` (home, conversation,
  changes/write turn, 90×26, 76×22). Marker checks confirm header stats, user blocks,
  `* Glob/Write` lines, composer row, hint line.
