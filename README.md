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
- `hex doctor` diagnostics
- Automated test suite (no paid API required for unit tests)

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

## Installation (Windows)

```powershell
git clone https://github.com/BluHExH/hex-cli.git
cd hex-cli
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
hex --help
hex doctor
hex                 # full-screen TUI
```

## Provider setup

```powershell
$env:OPENROUTER_API_KEY = "sk-or-..."
# or
$env:GROQ_API_KEY = "gsk_..."
# or local Ollama — set active_provider to ollama in ~/.hex/config.json
```

Keys can also live in `%USERPROFILE%\.hex\.env`.

## License

MIT — see [LICENSE](LICENSE).
