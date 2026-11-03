# HEX CLI 2.1.3 — Reference Fidelity Hardening

A second pass over the `hex-cli-ui.png` specification (1672×941 OpenCode reference) that
repairs what the 2.1.2 visual match left broken or approximate. HEX branding retained
throughout; OpenCode remains a structural reference only.

## What was actually broken in 2.1.2 (and how it was found)

### 1. Top header and status bar never rendered any text
`#top-header` had `height: 1` **plus** `border-bottom`, and `#bottom-status` had `height: 1`
plus `border-top`. Textual's border-box leaves zero content rows in both cases, so every
version of the header/status widgets rendered an empty line. Diagnosed by calling
`render_line(0)` on a mounted `AppHeader` — returned 160 spaces while `set_meta` had
already received real data.

**Fix (hex_cli/tui/theme.py):** both bars now use `height: 2` (1 text row + 1 border row),
which matches the reference: one text line above/below a divider line.

### 2. Git branch chip read the wrong repository
`HexApp._git_info()` ran `git rev-parse`/`git rev-list` with **no `cwd`**, so it inspected
the process's launch directory, not the app workspace (a call from a temp workspace
returned 91 — the count of the host repo). Now an instance method pinned to
`cwd=str(self.workspace)`, guaranteed read-only; the header shows `⎇ <branch> <count>`.

### 3. Multi-turn tool flow silently skipped tools
`MockProvider.complete` summarized `Tool results:…` whenever *any* tool message existed in
`messages`. On turn 2 the turn-1 history already contains one, so the model "summarized"
stale results and never issued the requested `write_file` — no Edit card, changes rail
stayed `0 files`, and no file deltas appeared. Now it summarizes only when
`messages[-1].role == "tool"`. Verified: WRITE turn issues `write_file`, produces the Edit
card, `Changes 1 files`, and a green `+46` delta row.

### 4. Tool durations were hardcoded `0.0s`
`AgentRunner` now times `tools.execute` with `time.monotonic()` and attaches real
`duration` to every event; timeline cards and Tools Activity render the true value
(e.g. `● Edit 0.1s`).

### 5. Windows clock crash + format drift
`strftime("%-I")` is not supported on Windows and crashed right-rail updates. Clocks now
use `"%I:%M %p".lstrip("0")` (e.g. `11:19 PM`), matching the reference. The context meter
uses one-decimal formatting (`0.2K / 120K`).

## Reference-alignment polish kept/finished in this pass
- Header: `⬡ HEX CLI …path │ ⎇ main 2 · mock/mock-smart ● Agent ⚙`
- Status bar: `● Ready · mock/mock-smart · ⌂ path · Ctrl+K Command Palette · Ctrl+L Sidebar · Ctrl+Enter Submit · Esc Cancel`
- Left rail: violet context bar `#7c6cf0`, `Ctrl+⇧+S` label
- Timeline: violet welcome banner (`✦ Welcome to HEX` + `● mock/mock-smart` pill)
- Composer: toolbar with `⬤ Auto` chip and violet `↵ Enter ▸` chip
- New bindings: `ctrl+k` → palette, `ctrl+enter` → submit current composer input

## Verification

- `pytest`: 19 passed (layout + version-consistency + tool/permission/session suites)
- Regenerated `docs/screenshots/ref_match_*.svg` (160×45 home/conversation/changes,
  100×30 medium, 80×24 narrow) via `scripts/capture_tui_screens.py`; the script creates a
  real temp git repository (two commits, explicit identity) so the header chip shows
  genuine data, and `.hex/config.json` with `permission_mode: allow` so tool calls are
  exercised end-to-end.
- Marker checks on the changes screen: `⬡ HEX`, `⎇ main`, `Changes 1 files`,
  `src/demo_generated.py`, `+46`, `List list_dir ✓ Completed · 0.0s`, `● Edit 0.1s`,
  `Tools Activity`, `Session Info`, `☑ Auto-save enabled`, status hints — all present.

## Known terminal limitations (unchanged)
- True alpha gradients and avatars are impossible in a text grid; approximated with pill
  chips and solid accents.
- SVG screenshots use the Fira Code font stack; emoji/octants render per terminal.
