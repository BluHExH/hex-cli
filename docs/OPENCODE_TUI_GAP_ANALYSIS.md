# HEX CLI — TUI Gap Analysis (Stage 1)

**Product:** HEX CLI  
**Company:** NeonBuild  
**Brand:** Powered by HEX  
**HEX version audited:** v1.0.0 (`67763ac`)  
**Reference product (UX only):** OpenCode terminal TUI ([opencode.ai/docs/tui](https://opencode.ai/docs/tui/), [anomalyco/opencode](https://github.com/anomalyco/opencode) `packages/tui`)  
**Date:** 2026-11-01  
**Stage:** Audit only — **no application code changes in this stage**

---

## 1. Executive summary

HEX CLI is a **real** Python/Textual coding-agent TUI with providers, agents, tools, sessions, permissions, streaming hooks, file picker, command palette, and offline identity. It is **not** feature-parity with OpenCode’s native TUI.

OpenCode’s TUI is a purpose-built terminal client (Solid/TS in `packages/tui`) with a mature layout language: session routes, leader-key chords (`ctrl+x`), configurable `tui.json`, fuzzy `@` file attach with picker UX, tool detail toggles, git-backed undo/redo, session tabs/timeline direction, and dense but readable conversation chrome.

HEX’s TUI is a single `HexApp` screen composed of header + left sidebar + chat scroll + activity bar + composer. The **bones** match the reference workflow (sidebar / chat / prompt). The **gaps** are mainly:

1. **Layout density & vertical use of space** — welcome is large ASCII text in the scroll view, but conversation/message chrome, tool presentation, and sidebar information architecture remain simpler and less “productized.”
2. **Interaction model** — OpenCode uses a **leader key** and a large keybind surface; HEX uses fewer global bindings and slash/palette hybrids.
3. **Tool & streaming presentation** — HEX emits real tool status and optional token streams; OpenCode’s tool details, diff_style, and message chrome are richer.
4. **Session UX** — HEX has sessions + disk persistence; OpenCode documents tabs, timeline, fork, rename, interrupt-on-escape, child sessions.
5. **Verification** — many HEX UI paths are **code-complete** with unit/pilot tests, but **Windows interactive terminal** validation remains incomplete in CI/sandbox.

This document is the specification input for later implementation stages. It deliberately does **not** claim parity.

---

## 2. Repository audit (HEX CLI v1.0.0)

### 2.1 Entry points & runtime

| Area | Location | Observed behavior |
|------|----------|-------------------|
| CLI | `hex_cli/main.py` | Typer CLI; launches TUI |
| TUI run | `hex_cli/tui/app.py` → `run_tui()` | Builds `HexApp`, loads config/dotenv |
| Version | `hex_cli/__init__.py` | `1.0.0` |
| Config | `hex_cli/config.py`, `~/.hex/` | Providers, selected model, project config |
| Credentials | `hex_cli/providers/credentials.py` | `~/.hex/credentials.json` |

### 2.2 Textual architecture

```
HexApp (App)
├── HeaderBar
├── Horizontal
│   ├── Sidebar (dock left, width 28)
│   └── Vertical #chat-container
│       ├── ChatLog (#chat-log)
│       ├── ActivityBar (#activity-bar)
│       └── InputPanel (#composer)
│           ├── meta (agent/model)
│           ├── slash suggestions
│           ├── PromptTextArea + Send + Stop
│           └── footer hints
└── footer-bar
```

- **Single screen** — modals for palette, file picker, providers, models, permissions, help.
- **State** — `SessionState` in `tui/state.py`; agent work via `@work(thread=True)`.
- **CSS** — `tui/theme.py` (`HEX_CSS`) + optional theme packs in `tui/themes.py`.

### 2.3 Component inventory (existence ≠ proven interactive quality)

| Component | File(s) | Role |
|-----------|---------|------|
| Sidebar | `widgets/sidebar.py` | Sessions, new session, project, agent, model, provider, git, status |
| Chat | `widgets/chat.py` | Welcome ASCII, message Static widgets, stream update helpers, tool lines |
| Composer | `widgets/input_panel.py` | `PromptTextArea` Enter/Shift+Enter, Send/Stop, slash suggest |
| Activity | `widgets/activity_bar.py` | Spinner + phase from busy/tool events |
| Tool card | `widgets/tool_card.py` | Expandable card model; chat path often uses status lines |
| Palette | `widgets/command_palette.py` | Filterable Ctrl+P actions |
| File picker | `widgets/file_picker.py` + `file_index.py` | Fuzzy list + preview |
| Dialogs | `dialogs.py`, `provider_dialogs.py` | Help, select, connect, model browser |
| Agent | `agent/loop.py` | Tool loop, cancel, stream-optional chat |
| Providers | `providers/*` | Registry, catalog, credentials |
| Sessions | `sessions/store.py` | Disk persistence |
| Offline ID | `knowledge/identity.py` | NeonBuild / Powered by HEX FAQ |
| Permissions | `permissions.py` | Risk + UI ask bridge |
| Changes | `changes/tracker.py` | Undo/redo session-local |

### 2.4 Tests present (automated)

Under `tests/`: stage2–5/7, agent, permissions, filesystem, chat IDs, composer pilot/submit, identity, provider picker, activity.  
**Evidence:** pilot tests cover Enter submit, empty reject, Send click, Shift+Enter path in headless Textual.  
**Not evidence of:** live Windows Terminal mouse/resize/stream quality.

---

## 3. OpenCode TUI reference analysis

Sources used (public docs + GitHub structure; **not** a full local clone of every TSX route):

- Docs: [TUI](https://opencode.ai/docs/tui/), [Keybinds](https://opencode.ai/docs/keybinds/), [CLI](https://opencode.ai/docs/cli/), [Commands](https://opencode.ai/docs/commands/)
- Repo signals: `packages/tui` (app/routes), issues/PRs on session sidebar/tabs, tool details

### 3.1 Documented OpenCode TUI behaviors

| Topic | Documented behavior |
|-------|---------------------|
| Launch | `opencode` or `opencode /path` opens project TUI |
| Prompt | Type message; **Enter** submit; **Shift/Ctrl/Alt+Enter** or **Ctrl+J** newline |
| `@` files | Fuzzy file search; content attached to prompt |
| `!` shell | Leading `!` runs shell into conversation |
| Slash | `/help`, `/connect`, `/models`, `/new`, `/sessions`, `/undo`, `/redo`, `/export`, `/compact`, `/editor`, `/details`, `/thinking`, … |
| Leader | Default **`ctrl+x`** then chord (n=new, l=sessions, m=models, …) |
| Palette | **`ctrl+p`** command list |
| Config | `tui.json`: theme, keybinds, scroll, `diff_style`, mouse, attention/notifications |
| Interrupt | `session_interrupt` → **escape** (documented) |
| Undo/redo | Git-backed file restore for undo/redo |
| Sidebar/sessions | Session list / tabs direction in product discussion; layout stores sidebar width |

### 3.2 Stack difference (important)

OpenCode TUI is **not Textual**. It is a dedicated TS terminal UI package. HEX cannot “copy widgets”; it must **recreate UX patterns** in Textual with NeonBuild/HEX branding.

### 3.3 Access limitations

- No interactive OpenCode binary was run in this audit environment.
- Visual claims about pixel-perfect proportions come from docs, issues, and architectural descriptions—not side-by-side live screenshots in this sandbox.
- Windows Terminal screenshots of HEX were **not** captured here (no interactive Windows host).

---

## 4. Feature comparison table

| Feature | OpenCode Behavior | HEX Current Behavior | Gap | Required Improvement | HEX files involved |
| ------- | ----------------- | -------------------- | --- | -------------------- | --- |
| Full-screen TUI | Native full terminal client | Textual `App` full screen | Medium — structure OK, density/polish lower | Tune CSS proportions, message density, empty-state vertical centering without wasting composer height | `theme.py`, `app.py`, `chat.py` |
| Sidebar | Session-centric, configurable width, rich session status | Fixed width 28; sessions + meta | Medium | Session search, busy indicators per session, clearer hierarchy, optional collapse animation | `sidebar.py`, `state.py` |
| Welcome | Minimal product home / session empty state | Large ASCII HEX + NeonBuild lines in `ChatLog` | Low–Medium | Keep large brand; improve vertical rhythm so composer stays primary; avoid “logo only feels small” on huge terminals | `chat.py`, `theme.py` |
| Composer | Multiline, Enter submit, multi-key newline, model/agent context | `PromptTextArea` priority Enter/Shift+Enter/Ctrl+J; Send/Stop | Low (logic); Medium (UX chrome) | Stash, clearer focus ring, @ autocomplete popup (not only modal picker) | `input_panel.py` |
| Enter / newline | Documented `input_submit` / `input_newline` | Implemented + pilot-tested | Low | Windows Terminal verification | `input_panel.py`, `tests/test_composer_*` |
| Command palette | Ctrl+P full command list | Ctrl+P filterable palette | Low–Medium | Expand actions; align naming with slash set | `command_palette.py`, `app.py` |
| Leader key | Ctrl+X chord system | No leader layer | High (discoverability) | Optional HEX leader map **or** document pure Ctrl+ shortcuts consistently | `app.py` BINDINGS |
| `/` slash | Rich built-ins + custom command files | Many `/` handlers in `handle_prompt` + suggest list | Medium | Custom project commands UX parity; consistent help | `app.py`, `commands_ext/` |
| `@` files | Inline fuzzy + attach | Modal picker + `@path` inject | Medium | Inline `@` popup while typing (OpenCode-like) | `file_picker.py`, `input_panel.py` |
| `!` shell | First-class | Implemented permission-gated | Low | Surface in help/welcome hints | `app.py` |
| Providers/models | `/connect`, `/models`, leader chords | `/provider` SelectDialog, `/models` browser, connect dialog | Medium | Unified status + multi-provider UX polish | `stage2_mixin.py`, `provider_dialogs.py` |
| Agents | Cycle/list keybinds | build/plan/explore/general; click/cycle | Medium | Visible agent switcher control, Shift+Tab cycle | `sidebar.py`, `agents/` |
| Sessions | List, fork, timeline, tabs direction | In-memory + disk save/load; sidebar switch | High | Rename, search, fork, status dots, optional tabs | `sessions/`, `sidebar.py` |
| Streaming | Progressive assistant text | Hooks + `begin_assistant_stream` / token update | Medium | Markdown/code fence rendering; avoid double-print; stronger cancel UX | `chat.py`, `agent/loop.py`, providers |
| Activity / thinking | Thinking blocks toggle; status | `ActivityBar` spinner from real phases | Medium | Tie phases more tightly; optional “thinking” fold | `activity_bar.py` |
| Tool UI | Details toggle, structured cards | Status lines + `ToolCard` widget underused | High | Mount real expandable cards per tool event; `/details` equivalent | `tool_card.py`, `chat.py`, `app.py` |
| Permissions | Explicit approve flow | Dialog + PermissionManager | Medium | Richer card (path/cmd preview) always | `dialogs.py`, `permissions.py` |
| Diff review | diff_style config; review UX | `/diff`, ChangeTracker, accept/reject APIs | Medium | In-chat diff widgets + mouse accept/reject | `changes/tracker.py`, chat widgets |
| Undo/redo | Git-backed | Session-local tracker redo | High | Optional git-backed undo when repo present | `changes/tracker.py` |
| Themes | `tui.json` theme packs | hex-dark/light/high-contrast | Medium | Persist selection; more packs; runtime switch reliability | `themes.py`, config |
| Mouse | Documented `mouse: true` | Buttons/lists/clicks implemented | Medium | Windows interactive verification | multiple widgets |
| Offline identity | N/A (always online product) | Offline FAQ (NeonBuild / Powered by HEX) | HEX-unique | Keep; never present as model reasoning | `knowledge/identity.py` |
| Notifications | Attention sounds/desktop | Missing | Low priority | Optional later | — |
| Multi-tab sessions | Product direction / issues | Single view + switch | High | Stage carefully; high complexity | sessions + app |

---

## 5. Visual design audit

### Why HEX can feel “small” or not OpenCode-like

1. **Conversation is a stream of `Static` blocks** — OpenCode’s message chrome (roles, tool folds, spacing) reads denser and more intentional.
2. **Sidebar is metadata-heavy, interaction-light** — agent/model are text rows; OpenCode treats model/agent as first-class switchers.
3. **Welcome lives inside the scroll region** — ASCII HEX is large in character cells, but on a tall terminal the **empty scroll + small effective focus on the composer** can still feel sparse or “logo in a void.”
4. **Tool cards exist as a class** but the default path often posts **one-line tool status**, so the UI looks closer to a log than an agent workbench.
5. **Borders/colors** — HEX dark theme is coherent (`#0b0f14` / purple accent) but lacks OpenCode’s multi-theme maturity and diff layout modes.
6. **Header + footer + activity + composer** stack reduces chat viewport vs a more aggressive OpenCode-style content-first split.

### Brand identity (must remain)

- Product name: **HEX CLI**
- Company: **NeonBuild**
- Tagline: **Powered by HEX**
- Never use OpenCode as HEX’s product name in UI or commits

### Layout targets for later stages

- Sidebar ~22–30 cols, collapsible, session list primary  
- Chat `1fr` with consistent message padding  
- Composer always visible, ≥5–8 rows usable  
- Welcome: brand block vertically balanced **above** the fold without shrinking the composer  
- Tool events as cards, not only log lines  

---

## 6. Interaction audit

Legend: **IT** = implemented + automated test evidence · **I** = implemented in code · **P** = partial · **M** = missing · **NT** = not interactively tested on Windows in this audit

| Interaction | Status | Evidence / notes |
|-------------|--------|------------------|
| Enter sends | **IT** | Pilot `test_composer_pilot.py` |
| Shift+Enter newline | **IT** | Pilot |
| Empty submit rejected | **IT** | Pilot |
| Send button | **IT** | Pilot click `#btn-send` |
| Stop / cancel | **I** | Stop button + `action_stop_agent`; **NT** live stream cancel |
| Slash suggestions | **I** | InputPanel filter; **NT** full keyboard nav feel |
| Ctrl+P palette | **I** | CommandPalette; **NT** |
| Ctrl+F file picker | **I** | FilePicker; unit fuzzy tests |
| Sidebar new session | **I** | Button message; **NT** |
| Session click switch | **I** | `sess-*` click; **NT** |
| Agent/model click | **I** | Sidebar messages; **NT** |
| `/provider` picker | **I** | SelectDialog path; registry tests |
| `/models` | **I** | Model browser worker |
| Permissions dialog | **I** | Bridge + dialog; unit permission tests |
| Diff accept/reject UI | **P** | Tracker APIs; weak in-chat controls |
| Mouse text selection in composer | **I** (TextArea) | **NT** Windows Terminal |
| Terminal resize | **P** | Textual handles layout; **NT** |
| Offline identity | **IT** | `test_identity.py` |
| Live provider streaming | **P** | Code path; **NT** without API in sandbox |

**Broken (known historical):** Enter-to-send was broken before v0.8.0 due to TextArea consuming Enter; fixed via `PromptTextArea` priority bindings. Treat regressions as high risk when touching the composer.

---

## 7. Architecture audit

### Strengths

- Clear separation: providers, agent loop, tools, permissions, sessions, TUI widgets  
- UI hooks from agent → `call_from_thread` keep Textual on the main thread  
- Unique chat widget IDs (monotonic + UUID) mitigate DuplicateIds  
- Offline identity modular and non-network  

### Limitations / risks

1. **`app.py` size (~1100+ lines)** — slash routing, palette, sessions, agent UI mixed; hard to evolve layout without regressions.  
2. **ToolCard vs log lines** — dual presentation paths; cards under-mounted.  
3. **Streaming** — provider `stream_chat` + loop rebuild of `ChatResponse` is fragile across providers; fallback to non-stream must not double-post.  
4. **No leader-key layer** — discoverability gap vs OpenCode docs.  
5. **Session model** — weaker than OpenCode’s session graph/tabs direction.  
6. **Git undo** — OpenCode documents git-backed undo; HEX redo is local tracker only.  
7. **Windows** — paths/editor considered; full Terminal UX unproven in CI.  
8. **Redundant help surfaces** — help dialog, slash list, palette, README can drift.

### Fragile patterns to avoid “rewriting blindly”

- Composer key bindings (priority matters)  
- `call_from_thread` + `Event` for permissions  
- Chat child ID uniqueness on clear/new session  

---

## 8. Missing and broken features (priority-ordered)

### P0 — User-visible coding-agent feel

1. Expandable **tool execution cards** for every real tool event  
2. Stronger **streaming + markdown/code** presentation  
3. **In-chat diff** review with accept/reject  
4. Composer **inline `@` autocomplete**  
5. Windows Terminal **interactive** validation checklist  

### P1 — Navigation & layout

6. Full-screen **proportion pass** (sidebar/chat/composer)  
7. Session search, rename, busy indicators  
8. Consistent **keybind map** (optional leader)  
9. Permission cards with full target preview  

### P2 — Parity stretch

10. Git-backed undo/redo when `.git` exists  
11. Theme persistence + more packs  
12. Session tabs / parallel session UX (high complexity)  
13. Desktop notifications (optional)  

### Not bugs — intentional HEX differences

- Offline identity (NeonBuild / Powered by HEX)  
- Textual stack vs OpenCode TS TUI  
- No claim of OpenCode product identity  

---

## 9. Prioritized development roadmap

> Implement in **stages**. Each stage ends with tests + Windows interactive notes + GitHub push under **HEX CLI** identity.

### Stage A — Layout & conversation chrome (next)

- **Objectives:** Full-terminal proportions; message spacing; welcome/composer balance  
- **Features:** CSS grid/dock pass; message widgets; reduce chrome clutter  
- **Likely files:** `theme.py`, `chat.py`, `app.py`, `sidebar.py`, `input_panel.py`  
- **Risks:** Composer Enter regressions  
- **Acceptance:** Welcome brand large; chat fills width; composer ≥5 rows; no startup spam  
- **Tests:** Snapshot/layout unit where possible; pilot composer; **interactive Windows checklist**  

### Stage B — Tool cards & activity truthfulness

- **Objectives:** Every tool call → card with status/output expand  
- **Features:** Mount `ToolCard`; map tool names to titles; activity bar sync  
- **Files:** `tool_card.py`, `chat.py`, `app.py`, `agent/loop.py`  
- **Risks:** Scroll performance on large outputs  
- **Acceptance:** No fake stages; only real tool events  
- **Tests:** Tool status transitions; cancel  

### Stage C — Streaming & markdown

- **Objectives:** Progressive assistant render; code fences; stop reliability  
- **Files:** `chat.py`, `agent/loop.py`, providers, `activity_bar.py`  
- **Acceptance:** Stream updates single bubble; cancel stops work  
- **Tests:** Mock stream events; double-post regression  

### Stage D — Composer context (`@`, slash, palette)

- **Objectives:** Inline `@` fuzzy; palette completeness; help sync  
- **Files:** `input_panel.py`, `file_picker.py`, `command_palette.py`  
- **Acceptance:** `@` without always opening full modal  

### Stage E — Permissions & diff review UI

- **Objectives:** Permission card UX; in-chat diff accept/reject  
- **Files:** `dialogs.py`, `changes/tracker.py`, new diff widget  
- **Acceptance:** No tool runs before approve  

### Stage F — Sessions UX

- **Objectives:** Search, rename, indicators; optional tabs later  
- **Files:** `sessions/`, `sidebar.py`, `state.py`  

### Stage G — Keybinds & polish

- **Objectives:** Documented shortcut map; optional leader; theme persist  
- **Files:** `app.py`, config, `themes.py`  

---

## 10. Testing strategy

### Automated (CI-friendly)

- Keep composer pilot tests as **gate** for Enter/Send  
- Add tool-card state machine tests  
- Identity + provider registry remain mandatory  
- Prefer headless Textual `run_test` for focus/click  

### Interactive (required on Windows before calling UX “done”)

On `D:\hex-cli` in Windows Terminal:

1. Launch `hex` — full-screen layout, large HEX welcome  
2. Enter / Shift+Enter / Send / Stop  
3. Mouse: sidebar session, New Session, Send, palette, file picker  
4. `/provider`, `/models`  
5. Offline: “Who are you?”, “Who built you?”  
6. With API: stream tokens, tool lines/cards, permission dialog  
7. Resize terminal width/height  

### Evidence rules

- **PASS** only with test output or recorded interactive checklist  
- **NOT TESTED** if only instantiated widgets  

---

## 11. Known limitations of this audit

1. No live OpenCode TUI session was operated here.  
2. No HEX screenshots from Windows Terminal were captured here.  
3. OpenCode source is TypeScript TUI — comparison is **UX/workflow**, not line-level port.  
4. Some OpenCode features (tabs, attention sounds) are product-evolving; treat docs/issues as directional.  
5. HEX v1.0.0 code was inspected as of commit `67763ac`; local uncommitted user changes at `D:\hex-cli` may differ until `git pull`.  

---

## 12. Stage 1 conclusion

HEX CLI already has a **credible coding-agent backend and a workable Textual shell**. Closing the gap to an OpenCode-**level** terminal experience is primarily a **presentation and interaction productization** problem: tool cards, message chrome, session UX, composer context, keybind discoverability, and verified Windows Terminal behavior—not a greenfield rewrite.

**Next stage should start with Stage A (layout & conversation chrome) + Stage B (tool cards),** using this document as the acceptance baseline.

---

*Document identity: HEX CLI / NeonBuild / Powered by HEX. OpenCode is cited only as an external UX reference.*
