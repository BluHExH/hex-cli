# HEX CLI 2.1.2 — Visual match report (reference image)

## Source of truth
Attached OpenCode workspace screenshot (structure + density). Branding is HEX only.

## Layout parity

| Region | Reference | HEX 2.1.2 | Match |
|--------|-----------|-----------|-------|
| Top header | brand · path · model · Agent | same structure | **Close** |
| Left rail | Session / Workspace / Context bar / Tools / Permissions / Recent / Help | same sections | **Close** |
| Center tabs | Session 1 × + | session title chip + | **Close** |
| Welcome card | gradient banner | ASCII box (no true gradient) | **Partial** |
| User / agent messages | avatar + timestamp | label + timestamp | **Close** |
| Tool cards | bordered, line preview, Completed | box-drawing cards | **Close** |
| Composer | Ask anything + chips + Enter | Input + toolbar row | **Close** |
| Right: Changes / Activity / Info | present | present + real data | **Close** |
| Bottom status | brand · Ready · model · path · shortcuts | same order | **Close** |

## Technical limitations (cannot be exact in Textual terminal)
1. **No true CSS gradients** on the welcome banner (reference uses purple wave graphic).
2. **No circular avatar images** — text bullets used instead.
3. **No anti-aliased icons** — Unicode symbols approximate file/tool glyphs.
4. **Font metrics** depend on the host terminal font; spacing is character-cell based.
5. **OS terminal PNG capture** was not available in the build environment; validation used Textual’s cell-buffer SVG export (`docs/screenshots/ref_match_*.svg`), which mirrors the same rendered grid the TUI shows.

## Screenshots captured
- `docs/screenshots/ref_match_home_160x45.svg`
- `docs/screenshots/ref_match_conversation_160x45.svg`
- `docs/screenshots/ref_match_medium_100x30.svg`
- `docs/screenshots/ref_match_narrow_80x24.svg`

## Tests
`pytest -q` — all existing tests including TUI layout suite.
