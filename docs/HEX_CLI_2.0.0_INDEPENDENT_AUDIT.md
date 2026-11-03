# HEX CLI 2.0.0 — Independent Technical Audit

**Audit date:** 2026-11-03  
**Mode:** Read-only (no application fixes, no commits, no pushes)  
**Auditor scope:** Verify delivery claim for commit `c11018ea3cb5d5920427d9c4ac434087a0f3af80`

**Skill reference:** OpenCode Expert Skill **v1.1.1**  
**OpenCode pin:** `ff90ed91607cabf420a369e9009539c1aa0932af`

---

## 1. Executive summary

HEX CLI 2.0.0 is a **real structural rebuild** of the Python package layout around agent/providers/tools/permissions/sessions. Core unit tests **pass (8)**. Several **release-integrity defects** make the published tree **inconsistent and not install-clean** relative to the delivery narrative:

| Issue | Severity |
|-------|----------|
| `pyproject.toml` still declares **version 1.5.1** | **HIGH** (release integrity) |
| Console script points to `hex_cli.main:app` but only `main()` exists | **CRITICAL** (broken `pip install` entry) |
| Root `README.md` still documents **v1.5.x** feature set | **HIGH** (docs lie vs code) |
| TUI depends on Textual; environment without Textual cannot import TUI | expected; interactive TUI **NOT TESTED** |
| MCP is a non-functional placeholder | correctly limited in MCP module text; must not be marketed as runtime |
| Shell tool uses `shell=True` | **HIGH** security when permissions allow |

**Overall audit verdict: PARTIAL / CONDITIONAL**

The architecture direction matches Skill guidance (native Python, JSON sessions, tool+permission boundary, no server port). The **release packaging and documentation did not fully complete** the 2.0.0 cutover.

---

## 2. Repository and release verification

| Check | Result |
|-------|--------|
| Branch | `main` |
| Local HEAD | `c11018ea3cb5d5920427d9c4ac434087a0f3af80` |
| Remote `origin/main` HEAD | **same SHA** (verified via `git ls-remote`) |
| Working tree at audit start | clean relative to that commit (aside from this audit artifact if added later) |
| `hex_cli.__version__` | **`2.0.0`** |
| `pyproject.toml` `[project].version` | **`1.5.1`** — **MISMATCH** |
| Entry point | `hex = "hex_cli.main:app"` vs `def main` only — **BROKEN** |
| Package structure | New modules present (`agent/runner.py`, `tools/`, `sessions/`, …); legacy `agent/loop.py` **absent** |

**Evidence commands:**
```text
git rev-parse HEAD  → c11018ea3cb5d5920427d9c4ac434087a0f3af80
git ls-remote … refs/heads/main → c11018ea3cb5d5920427d9c4ac434087a0f3af80
python3 -c "import hex_cli; print(hex_cli.__version__)" → 2.0.0
```

---

## 3. Architecture review (implementation, not docs alone)

### Agent (`hex_cli/agent/runner.py`)
- **Lifecycle:** `run_turn` → compact → loop `complete` → optional tool executes → append tool messages → repeat until no tool calls or `max_tool_rounds`.
- **Termination:** break on text response; else “max tool rounds” message.
- **Cancellation:** **not implemented** (no cancel event/flag in runner).
- **Retry:** **not implemented** at runner level.
- **Error propagation:** tool errors become tool-role content; broad `except` only in TUI submit handler.
- **State:** returns full message list; session persistence is TUI’s responsibility.

Skill alignment: phase loop echoes SessionRunner *concept*; lacks drain/compaction-failure event richness of OpenCode pin.

### Providers
- **Mock:** deterministic READ/WRITE/LIST scripting; summarizes after tool messages.
- **OpenAI-compat:** single `httpx` POST; tools mapped to functions; `raise_for_status()`; timeout 120s.
- **Streaming:** `stream_text` **chunks final text** after non-stream complete — not true token SSE.
- **Credentials:** env only via `HexSettings.api_key()` — good. Missing key falls back to mock.
- **Gaps:** no retry/backoff; tool messages not mapped to OpenAI tool-role schema on subsequent turns (may break real providers).

### Tools
- **PathGuard:** resolve + `relative_to(root)` — blocks `..` and absolute outside root (**tested**).
- **Symlink:** symlink to outside fails resolve/`relative_to` (**tested** → deny).
- **Shell:** `subprocess.run(..., shell=True, timeout=60, output cap 20k)` — workspace cwd only; **still full shell**.
- **Search:** rglob skips dot-segments in path parts; regex user-controlled (ReDoS residual risk).

### Permissions
- Modes: allow / deny / prompt.
- Auto-allow read/list/search tools.
- Prompt without prompter → **deny** sensitive ops (**tested**).
- TUI constructs gate with settings mode but **does not inject an interactive prompter** → write/shell denied unless mode=`allow`.

### Sessions
- JSON under `.hex/sessions/`; write via `.tmp` + `replace` — atomic on same filesystem.
- Corrupt JSON → `json.loads` raises (**tested**); no soft recovery.
- No file locking → concurrent writers last-write-wins.
- Isolation by session id files — OK for single-user CLI.

### Changes
- Journal of before/after; `restore_last` pops stack and writes/deletes.
- No multi-file transactional restore; no disk snapshot tree (Skill snapshot service not ported — intentional thinner design).

### Context
- Char-budget trim keeps first message + recent tail; inserts system note.
- Can drop middle tool traces — information loss expected; not OpenCode SessionCompaction.

### TUI
- Textual `App` with sidebar static, RichLog, Input, status line.
- Sync `run_turn` on input thread — UI may freeze on long provider calls.
- Import requires `textual` installed; audit env without it → `ModuleNotFoundError` (import-only check failed until dep present).
- Interactive run **NOT TESTED**.

### Advanced
| Claim | Reality |
|-------|---------|
| MCP | `MCPClient.list_tools` returns `[]`; `call_tool` raises `NotImplementedError` |
| LSP | **No package** in 2.0 tree |
| Server API | Absent (appropriate) |

---

## 4. Feature implementation matrix

| Feature | Code present | Behavior verified | Notes |
|---------|--------------|-------------------|-------|
| Agent multi-step tools | Yes | Yes (mock) | No cancel |
| Mock provider | Yes | Yes | |
| OpenAI-compat HTTP | Yes | Structure only | No live API |
| True streaming | Partial | Code review | Fake chunking |
| File R/W/list/search | Yes | Yes | |
| Shell | Yes | Yes | Dangerous |
| Path jail | Yes | Yes | |
| Permissions | Yes | Yes | TUI prompter missing |
| Session save/load | Yes | Yes | |
| Change restore | Yes | Unit | |
| Context trim | Yes | Unit | |
| Textual TUI chrome | Yes | Import only | |
| MCP runtime | No | Placeholder | |
| LSP | No | — | |
| Installable `hex` console script | **Broken** | Entry mismatch | CRITICAL |

---

## 5. Test results

### Project suite
```text
cd hex-cli
PYTHONPATH=. python3 -m pytest -q --tb=line
→ 8 passed, 1 warning (unknown asyncio_mode in leftover/partial pyproject config)
```

### Isolated probes (temp dirs, no project mutation)
```text
Symlink escape read     → denied (ok=False, path escapes workspace)
Traversal ../           → denied
Absolute outside path   → denied
prompt mode write       → permission denied
prompt mode read        → allowed
shell echo              → runs when mode=allow
corrupt session JSON    → JSONDecodeError on load
main vs app attribute   → main True, app False
```

### Not tested
- Windows Terminal interactive TUI  
- Real provider credentials  
- Concurrent session writers  
- Long-run agent cancellation  

---

## 6. Security findings

| ID | Severity | Finding | Evidence | Impact |
|----|----------|---------|----------|--------|
| S1 | **HIGH** | Shell tool uses `shell=True` with full command string | `tools/shell.py` | Command injection / lateral movement if permissions allow or mode=allow |
| S2 | **HIGH** | Headless one-shot forces `permission_mode=allow` | `main.py` prompt path | Any tool including shell runs without prompt |
| S3 | **MEDIUM** | No interactive permission prompter in TUI | `tui/app.py` uses gate without prompter | Writes/shell blocked in prompt mode OR user switches to allow globally |
| S4 | **MEDIUM** | Provider tool-call args trusted into tools | runner passes `call.arguments` through | Malicious model can request writes/shell when allowed |
| S5 | **LOW** | Session/message content not sanitized for log/display | TUI writes tool output | Prompt-injection style UI confusion |
| S6 | **LOW** | Restore can delete file if `before is None` | `changes/tracker.py` | User-triggered data loss if journal wrong |
| S7 | **INFORMATIONAL** | API keys from env only | `config/settings.py` | Good practice |
| S8 | **INFORMATIONAL** | Path jail effective for tested escapes | isolated probes | Good baseline |

No CRITICAL remote RCE without user enabling allow-mode or approving tools; **CRITICAL packaging defect** is availability, not RCE.

---

## 7. Windows compatibility assessment

| Topic | Assessment |
|-------|------------|
| Path logic | `pathlib` used; not Windows-executed in this audit |
| Shell | `shell=True` behaves differently on Windows cmd vs POSIX |
| TUI | Textual + Windows Terminal **NOT TESTED** on Windows host |
| File locking | not implemented (same on all OS) |

**Verdict:** **NOT TESTED** on Windows. No claim of Windows interactive success.

---

## 8. Documentation consistency

| Document | vs code |
|----------|---------|
| `hex_cli/__init__.py` 2.0.0 | Matches intent |
| `pyproject.toml` 1.5.1 + old deps (typer, gitpython, …) | **Stale / wrong for 2.0 tree** |
| `README.md` | **Still 1.5.x changelog-style feature list** |
| `docs/ARCHITECTURE.md` | Describes 2.0 design (present) |
| MCP module docstring | Honest about non-implementation |

---

## 9. Skill effectiveness evaluation (v1.1.1)

| Skill guidance | HEX 2.0 response | Effective? |
|----------------|------------------|------------|
| Native Python/Textual, don’t port Effect/TS | Followed | **Yes** |
| Keep JSON sessions unless intentional SQL migration | JSON atomic store | **Yes** |
| Tool + permission boundary | Explicit gate + registry | **Yes** |
| Snapshot as recovery distinct from Git | Thin ChangeLog, not full snapshot service | **Partial adapt** |
| MCP HTTP exists upstream; HEX optional | Placeholder only | **Conservative / under-built** |
| LSP PARTIAL upstream | Omitted | **Yes** |
| Server not required for TUI | Omitted | **Yes** |
| Evidence discipline / no fake features | MCP honest; packaging/docs inconsistent | **Mixed** |

**Skill helped** modular boundaries and exclusion of server/LSP overclaim.  
**Skill did not prevent** incomplete release cutover (pyproject/README) or shell=True risk — those are engineering execution gaps, not Skill failures.

Skill score as design aid: **useful**. Skill score as release-quality enforcer: **not applicable** (Skill is research guidance, not a CI gate for HEX).

---

## 10. Defects register (document only — not fixed)

1. **CRITICAL:** Console script `hex_cli.main:app` invalid.  
2. **HIGH:** Version metadata split (2.0.0 code vs 1.5.1 pyproject).  
3. **HIGH:** README describes removed 1.x capabilities.  
4. **HIGH:** Shell `shell=True` under allow mode.  
5. **MEDIUM:** No agent cancellation.  
6. **MEDIUM:** OpenAI tool-result message shape likely incomplete for multi-round real APIs.  
7. **MEDIUM:** TUI blocks on synchronous provider calls.  
8. **LOW:** Corrupted session JSON hard-fails.  
9. **INFORMATIONAL:** True SSE streaming absent.

---

## 11. Overall verdict

**PARTIAL**

- **Confirmed:** Commit `c11018e…` is on `main` locally and remotely; new architecture modules exist; 8 unit tests pass; path jail and basic permissions work in isolated probes.  
- **Not confirmed:** Clean install via declared entry point; documentation accuracy for 2.0.0; Windows TUI; production provider tool loops; MCP/LSP product features.  

Treat 2.0.0 as an **architectural foundation with a failed packaging/docs cutover**, not a fully shippable polished release until defects 1–3 are fixed.

---

## Appendix — Commands run

```bash
git rev-parse HEAD
git ls-remote … refs/heads/main
PYTHONPATH=. python3 -m pytest -q --tb=line
python3 -c "import hex_cli; print(hex_cli.__version__)"
python3 -c "import hex_cli.main as m; print(hasattr(m,'main'), hasattr(m,'app'))"
# tempfile path jail / symlink / permission / shell / corrupt session probes
python3 -c "from hex_cli.tui.app import HexApp"  # failed without textual in bare env
```
