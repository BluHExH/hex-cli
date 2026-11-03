# HEX CLI 2.1.0 — UI/UX Redesign

## Design principles
- Professional dark developer tool, not a chatbot toy
- HEX accent (`#a78bfa`) on neutral surfaces
- Compact header + status; conversation is primary
- Structured tool activity (not raw dump)
- Responsive: sidebar collapses under ~100 columns
- Backend (agent/tools/sessions) unchanged

## Layout
1. **AppHeader** — brand, workspace, model, status, shortcut hints  
2. **SessionSidebar** — workspace, session, model, permissions, changes, recent  
3. **HomeScreen** — empty-state landing  
4. **ConversationTimeline** — user / assistant / tool / error  
5. **PromptComposer** — multiline TextArea, Ctrl+Enter send  
6. **StatusBar** — state + shortcuts  
7. **CommandPalette** — Ctrl+P modal  

## Theme
Central tokens in `hex_cli/tui/theme.py` (`HEX_THEME_CSS`).

## Shortcuts
| Key | Action |
|-----|--------|
| Ctrl+Enter | Send message |
| Ctrl+N | New session |
| Ctrl+B | Toggle sidebar |
| Ctrl+P | Command palette |
| Ctrl+L | Focus composer |
| Ctrl+C | Cancel turn / quit if idle |
| Ctrl+Q | Quit |
| ? | Help line in timeline |

## Responsive
- ≥100 cols: sidebar visible (unless toggled off)  
- <100 cols: sidebar hidden automatically  

## Screenshots
This environment does not provide OS-level terminal screenshots.  
Validation used Textual `run_test` pilot at 80×24 and 120×36.

## Limitations
- Permission dialog is not a full modal approve/deny UI yet (gate modes still apply)
- True OpenCode visual parity (Solid/TS components) is not claimed
- Screenshot PNGs not generated in CI sandbox

## Testing
- Backend regression suite retained  
- `tests/test_tui_layout.py` composition/narrow/submit smoke  
