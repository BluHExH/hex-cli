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
