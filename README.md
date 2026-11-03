# HEX CLI 2.1.1

Native **terminal** AI coding agent for software development.

- **Stack:** Python 3.11+ · Textual TUI (optional extra)
- **Brand:** HEX / NeonBuild — Powered by HEX
- **OpenCode:** external design reference only (not this product)

## Install

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -e ".[dev]"     # includes Textual for TUI + tests
# or minimal core:
pip install -e .
# TUI only extra:
pip install -e ".[tui]"
```

```bash
hex --help
hex --version
hex                    # starts TUI (requires textual)
hex "LIST ."           # headless one-shot (mock provider by default)
```

## Configuration

Workspace file: `.hex/config.json`

| Key | Default | Meaning |
|-----|---------|---------|
| `provider` | `mock` | `mock` or OpenAI-compatible HTTP |
| `model` | `mock-smart` | Model id |
| `api_base` | `""` | e.g. `https://api.openai.com/v1` |
| `permission_mode` | `prompt` | `prompt` · `allow` · `deny` |

Secrets via environment (never commit keys):

- `HEX_API_KEY` / `OPENAI_API_KEY` / `OPENROUTER_API_KEY`

## Tools

| Tool | Notes |
|------|--------|
| `read_file` / `list_dir` / `search_files` | Workspace-jailed; auto-allowed in prompt mode |
| `write_file` | Requires allow or interactive approval path |
| `run_shell` | **argv list, `shell=False` by default**; optional `use_shell=true` is explicit and gated |

## Sessions

Stored under `.hex/sessions/*.json` with atomic temp+replace writes.

## Permissions

Default `prompt` mode denies writes/shell unless a prompter allows them or mode is `allow`.

Headless:

```bash
hex --permission allow "READ README.md"
```

## TUI

- Enter sends a message
- Ctrl+C cancels an in-flight turn (or quits when idle)
- Ctrl+N new session
- Agent work runs in a **worker thread** so the UI stays responsive

## MCP / LSP

- **MCP:** interface placeholder only — **not** an operational MCP runtime in 2.1.1
- **LSP:** not included in 2.1.1

## Tests

```bash
pytest -q
```

## Architecture

See `docs/ARCHITECTURE.md`.

## Limitations

- True token SSE streaming is not fully implemented (provider may chunk final text)
- Shell without `use_shell` cannot expand globs/pipes (by design)
- Windows interactive testing depends on your terminal; CI may be Linux-only
- Not OpenCode feature-parity

## Version

**2.1.1** — packaging, docs, shell safety, cancellation, TUI workers

## TUI (2.1)

Professional layout with header, sidebar, home screen, conversation timeline, multiline composer (Ctrl+Enter), status bar, and Ctrl+P command palette. See `docs/HEX_CLI_2.1.1_UI_REDESIGN.md`.
