## HEX CLI v1.2.0

- Live assistant **token streaming** into one Markdown message
- Safe partial Markdown / code-fence rendering while streaming
- **Ctrl+Shift+C** copies the last fenced code block
- Smart auto-scroll (pauses when you scroll up)

## HEX CLI v1.1.0

- Full-screen layout polish (sidebar, conversation, composer)
- Expandable **tool execution cards** driven by real agent events
- Click/keyboard expand for tool output
- Activity bar synced to real tool phases

## HEX CLI v1.0.0

Professional terminal AI coding agent by **NeonBuild** (*Powered by HEX*).

### Highlights
- Full-size HEX welcome workspace
- Live **activity indicator** tied to agent/tool state
- Streaming responses when the provider supports it
- Tool execution status in the conversation
- **Stop** control during generation
- Offline product identity without an API key
- Provider/model pickers, sessions, permissions, undo/redo

### Quick start
```bash
pip install -e .
hex
```
Configure a provider with `/provider` or `/connect`.

## HEX CLI v0.9.0

- **Full-size welcome** with centered HEX branding (Powered by HEX · NeonBuild)
- **Offline identity** answers product questions without an API key
- **/provider** opens a selectable provider picker (keyboard + mouse)
- **/model** model browser remains fully functional
- Explore the full UI without configuring a provider

Offline examples: "Who are you?", "Who built you?", "What powers you?", "Can you work offline?"

## HEX CLI v0.8.0

- **Minimal startup** — no banner/debug spam in the conversation pane
- **Enter sends**, Shift+Enter / Ctrl+J newline (PromptTextArea priority bindings)
- **Send button** for mouse users
- Sidebar session / New session / agent / model clicks
- Headless pilot tests for submit, empty reject, send button

## HEX CLI v0.7.1 — stability

- Fixed corrupted multiline prompt composer module (critical)
- Structured tool execution lines with status / output preview
- Live token streaming hooks from agent → conversation UI
- Composer busy state + Ctrl+. stop awareness
- Regression tests: 42 unit tests passing


## Stage 3 — Coding agent

HEX runs a real agent loop with tools:

| Tool | Purpose |
|------|---------|
| `read_file` / `write_file` / `edit_file` / `apply_patch` | File operations (writes need approval) |
| `list_files` / `glob` / `search_text` | Explore and search the project |
| `run_command` / `run_tests` | Shell and tests (approval required) |
| `project_overview` / `detect_project_type` | Project awareness |
| `git_status` / `git_diff` | Git inspection |

Commands: `/plan` (no mutations), `/diff`, `/undo`, `/tools`, `/permissions`, `/init`.

Changes are tracked for review and undo. Secrets stay out of logs.

# HEX CLI

**HEX** is an AI coding agent that runs in your terminal. It understands natural-language development tasks, inspects your project, proposes changes, and executes tools only after you approve them.

Inspired by tools such as OpenCode and OpenHands, HEX is an original implementation focused on **permission-first security**, **Windows support**, and a clean modular architecture.

```
  ██╗  ██╗███████╗██╗  ██╗
  ██║  ██║██╔════╝╚██╗██╔╝
  ███████║█████╗   ╚███╔╝
  ██╔══██║██╔══╝   ██╔██╗
  ██║  ██║███████╗██╔╝ ██╗
  ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
  HEX CLI — AI Coding Agent
```

## HEX CLI v0.7.0

- Fuzzy **file picker** (`Ctrl+F` / `/files`) with preview and `@path` insert
- **Themes**: `hex-dark`, `hex-light`, `high-contrast` (`/theme <id>`)
- **External editor** compose (`Ctrl+E` / `/editor`, uses `HEX_EDITOR` / `EDITOR` / `VISUAL`)
- Session-local **redo** after undo (`Ctrl+Y` / `/redo`) — not a git reset
- Expanded help and command palette actions

## OpenCode parity notes (v0.6.2)

Closer to OpenCode TUI workflows:

| OpenCode | HEX |
|----------|-----|
| Ctrl+P command palette | Yes — filterable palette |
| Multiline composer Enter / Shift+Enter | Yes |
| `/` slash commands | Yes + custom commands |
| `!` shell into chat | Yes (permission-gated) |
| `@file` references | Yes (content injected, size-capped) |
| Sessions sidebar | Yes |
| Agents / models | Yes (`/agent`, `/models`, palette) |
| Export / compact | `/export`, `/compact` |
| Stop generation | Ctrl+. when busy |
| MCP / Skills / LSP | Present (stdio MCP, skills, LSP client) |

Not full OpenCode parity: no external `$EDITOR` compose, no redo/git-backed undo stack, no desktop notifications, no theme pack system, no team/multi-tab sessions.

## UI reconstruction (v0.6.1)

OpenCode-inspired full-screen layout:

- **Left sidebar** — HEX brand, sessions, new session, project path, agent, model, provider, git branch, online status
- **Main workspace** — conversation with distinct user / assistant / tool / system styles and welcome screen
- **Prompt composer** — large multiline input (Enter send, Shift+Enter newline, `/` slash suggestions, agent + model meta)
- **Keyboard** — Ctrl+N new session, Ctrl+B sidebar, Ctrl+P models, Ctrl+H help, Ctrl+Shift+A cycle agent

## Stage 5 — Multi-agent, MCP, Skills & Developer Ecosystem (v0.6.0)

- **Parallel subagents** — isolated contexts, concurrency limits, structured merge, cancellation
- **MCP client** — stdio transport, tool discovery, namespaced tools, approval-gated execution
- **Skills** — global + project skills (`SKILL.md`), agent-scoped activation
- **Custom commands** — markdown prompt templates with `{{args}}` substitution
- **LSP client** — initialize/shutdown, diagnostics, hover, definition, references, symbols
- **Git worktrees** — list/create/remove with permission checks
- **Tool cards** — expandable execution states (running/completed/failed/denied/cancelled)
- **Project config** — `.hex/config.json` overrides that cannot silently loosen permissions
- Commands: `/mcp`, `/skills`, `/worktree`, `/lsp`, plus user-defined slash commands

## Stage 4 — Professional agent experience (v0.5.0)

- **Persistent sessions** — save/restore conversations under `~/.hex/sessions/` (versioned JSON, no API keys stored)
- **Specialized agents** — Build, Plan, Explore, General with distinct system prompts and tool allow-lists
- **Streaming foundation** — native provider streaming with normalized events and honest non-stream fallback
- **Code review** — accept/reject individual files, external modification detection, unified diffs
- **Git tools** — branches, log, stage, commit, checkout (all approval-gated; no silent push/reset)
- **Developer intelligence** — basic syntax diagnostics, ignore-aware project search
- Commands: `/agent`, `/agents`, `/build`, `/plan`, `/explore`, `/save`, `/history`, `/session rename|delete|search`

## Features

- **Full-screen TUI** (Stage 1) — OpenCode-inspired terminal UI with header, sidebar, chat panel, and status bar
- Natural-language coding sessions in the project directory
- Multi-provider LLM support (OpenAI-compatible APIs, Ollama local models, OpenRouter, Groq)
- Built-in **free model presets** (OpenRouter `:free` models such as Nemotron 3 Ultra, Laguna, North Mini Code)
- Structured tool calling: list/read/search/write/edit files, run commands, git status/diff, tests
- **Permission-first** workflow — file writes and shell commands require approval (modal dialogs in TUI)
- Path traversal and symlink-escape prevention
- Diff previews before edits
- Project context awareness (respects common ignore patterns)
- `hex doctor` diagnostics
- Automated test suite (no paid API required for unit tests)



## Stage 2.5 — Professional TUI

HEX launches a full-screen Textual interface with:

- HEX ASCII banner on startup
- Header (brand, project, model, online/offline)
- Collapsible sidebar (sessions, project, provider, model)
- Chat workspace with distinct message styles and tool status
- Bottom multiline input (`Enter` send, suggestions on `/`)
- Commands: `/connect` `/models` `/providers` `/new` `/clear` `/sessions` `/help`
- Fixed: chat widget ID lifecycle (no DuplicateIds on clear/new session)

## Stage 2 — Providers & models

HEX opens **without** an API key. Inside the TUI:

| Command | Action |
|---------|--------|
| `/connect` | Choose provider and enter API key |
| `/models` | Browse / search models (F = free only) |
| `/providers` | List connection status |
| `/disconnect` | Remove stored credential |
| `/settings` | Show settings overview |

Supported providers: OpenRouter, OpenAI, Google Gemini, Groq, NVIDIA, Cerebras, Mistral, Anthropic, Ollama, Custom OpenAI-compatible.

Credentials are stored in `~/.hex/credentials.json` (owner-only permissions when the OS allows). Environment variables always override stored keys. Free models are labeled only when the provider marks them free (e.g. OpenRouter `:free`) or for local Ollama — paid models are never labeled free.

## Quick start (TUI)

```powershell
# After install + API key
$env:OPENROUTER_API_KEY = "sk-or-..."
hex                 # launches full-screen TUI
# or
hex chat
hex --classic       # old line-oriented prompt
```

### TUI keyboard shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+C` / `Ctrl+Q` | Quit |
| `Ctrl+L` | Clear conversation |
| `Ctrl+N` | New session |
| `Ctrl+P` | Provider / model picker |
| `Ctrl+B` | Toggle sidebar |
| `Ctrl+H` | Help |
| `Enter` | Submit prompt |
| `Ctrl+J` | Newline in prompt |
| `Escape` | Close dialog / focus input |

Slash commands still work inside the prompt: `/model`, `/provider`, `/status`, `/clear`, `/help`, `/exit`.

## Requirements

- **Python 3.11+** (3.12 recommended)
- **Git** (optional but recommended)
- An API key for a hosted provider **or** [Ollama](https://ollama.com) for local models
- Windows 10/11, macOS, or Linux

## Installation (Windows)

```powershell
# Clone
git clone https://github.com/BluHExH/hex-cli.git
cd hex-cli

# Virtual environment
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# If PowerShell blocks activation:
#   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
# Or run without activating:
#   .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
#   .\.venv\Scripts\hex.exe --help

python -m pip install --upgrade pip
pip install -e ".[dev]"

# Verify
hex --help
hex doctor
hex                 # full-screen TUI
```

### Run without activating the venv

```powershell
.\.venv\Scripts\hex.exe doctor
.\.venv\Scripts\hex.exe
```

### Linux / macOS

```bash
git clone https://github.com/BluHExH/hex-cli.git
cd hex-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
hex --help
hex
```

## Provider setup

HEX never stores API keys in the repository. Keys are read from environment variables or a `.env` file.

### Option A — Hosted API (OpenAI, Groq, OpenRouter)

**PowerShell:**

```powershell
$env:OPENAI_API_KEY = "sk-..."
# or
$env:GROQ_API_KEY = "gsk_..."
# or
$env:OPENROUTER_API_KEY = "sk-or-..."
```

**Or create `~/.hex/.env`:**

```
OPENAI_API_KEY=sk-...
```

Then:

```powershell
hex init          # creates ~/.hex/config.json
hex config        # inspect settings
hex doctor        # verify connectivity
```

### Option B — Local models with Ollama (free, offline)

1. Install [Ollama](https://ollama.com)
2. Pull a model: `ollama pull llama3.2`
3. Ensure the server is running: `ollama serve`
4. Switch provider:

```powershell
hex init
# Edit ~/.hex/config.json → set "active_provider": "ollama"
# Or in a session: /provider ollama
hex doctor
```

### Free-tier vs local models

| Option | Cost | Needs internet | Notes |
|--------|------|----------------|-------|
| Ollama | Free | No (after model download) | Runs on your machine; quality depends on model size |
| Groq free tier | Free quota | Yes | Fast inference; rate limits apply |
| OpenRouter | Varies | Yes | Many models; some free endpoints exist — check their docs |
| OpenAI | Paid | Yes | High quality; requires billing |

HEX does **not** claim that paid APIs are free. Always check the provider’s current pricing.

## Usage

```powershell
hex                 # interactive session in current directory
hex --version
hex --help
hex doctor          # environment & provider diagnostics
hex config          # show configuration
hex models          # list models (best-effort)
hex model gpt-4o-mini
hex init            # initialise ~/.hex
hex chat            # same as bare `hex`
```

### Interactive session

```
hex > Inspect this project, identify the main bug, explain your proposed fix,
      and ask before modifying any files.
```

Slash commands inside a session:

| Command | Action |
|---------|--------|
| `/help` | Show help |
| `/exit` | Quit |
| `/clear` | Reset conversation context |
| `/status` | Project & provider status |
| `/model <name>` | Switch model |
| `/provider <name>` | Switch provider |
| `/permissions` | Show permission modes |

## Permission model

Default behaviour:

| Action | Mode |
|--------|------|
| Read files | allow (within project) |
| Create files | ask |
| Modify files | ask (with diff preview) |
| Delete files | ask + extra confirmation |
| Run commands | ask |
| Git commit | ask |
| Git push | ask + high-impact confirmation |
| Deployment | ask + high-impact confirmation |

Configure modes in `~/.hex/config.json` under `"permissions"`. Values: `"allow"`, `"ask"`, `"deny"`.

### Security limitations (honest)

- Command execution uses the system shell with `cwd` set to the project root. A blocklist of dangerous patterns is **not** a complete sandbox.
- Approval prompts depend on an interactive terminal.
- Symlink and `../` traversal are blocked for file tools, but a malicious approved command could still affect the system.
- Do not run HEX as Administrator / root.
- Treat model output and repository text as untrusted; HEX ignores embedded instructions that try to override its security policy.

## Configuration

User config directory:

- Windows: `%USERPROFILE%\.hex\`
- Linux/macOS: `~/.hex/`

Files:

- `config.json` — providers, models, permissions, limits
- `.env` — optional API keys (never commit)

See `config.example.json` and `.env.example` in this repository.

## Architecture

```
hex_cli/
  main.py          # Typer CLI
  config.py        # Settings & paths
  permissions.py   # Path safety + approval
  context.py       # Project summary
  ui.py            # Rich terminal UI
  providers/       # OpenAI-compatible clients
  agent/           # Loop + system prompts
  tools/           # filesystem, commands, git
```

## Testing

```powershell
pip install -e ".[dev]"
pytest -q
```

Unit tests cover path traversal, symlink escape, permission approve/reject, file tools, tool-argument validation, config load/save, and agent dispatch. Network calls are mocked — **no paid API key is required**.

```powershell
pytest -q
# ........  (all should pass)
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `hex` not found | Ensure venv is activated, or use `.\.venv\Scripts\hex.exe` |
| Activation blocked | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| API key errors | `hex doctor`; set `$env:OPENAI_API_KEY` or `~/.hex/.env` |
| Ollama connection refused | Start `ollama serve`; check `base_url` is `http://localhost:11434/v1` |
| Rate limit / 429 | Wait and retry; lower model size; switch provider |
| Permission prompts never appear | Run in an interactive terminal (not piped) |

## Contributing

1. Fork and clone
2. Create a branch
3. Install with `pip install -e ".[dev]"`
4. Run `pytest -q` and fix failures
5. Open a pull request

Do not commit `.env`, API keys, or `*.hexbak` files.

## License

MIT — see [LICENSE](LICENSE).
