"""HEX CLI entry point — Typer application."""

from __future__ import annotations

import json
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.prompt import Prompt

from hex_cli import __version__, ui
from hex_cli.config import (
    AppConfig,
    ensure_config_dir,
    get_api_key,
    get_config_dir,
    get_config_path,
    load_config,
    load_dotenv_if_present,
    save_config,
)
from hex_cli.permissions import PermissionManager
from hex_cli.providers.base import ProviderError, create_provider

app = typer.Typer(
    name="hex",
    help="HEX CLI — AI coding agent for software development.",
    add_completion=False,
    no_args_is_help=False,
    invoke_without_command=True,
)


def _project_root() -> Path:
    return Path.cwd().resolve()


def _setup_permissions(config: AppConfig, root: Path) -> PermissionManager:
    pm = PermissionManager(config, root)
    pm.set_ask_callback(ui.ask_permission)
    return pm


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-V", help="Show version and exit"),
    classic: bool = typer.Option(
        False,
        "--classic",
        help="Use the classic line-oriented prompt instead of the full-screen TUI",
    ),
) -> None:
    if version:
        ui.print_version()
        raise typer.Exit(0)

    if ctx.invoked_subcommand is not None:
        return

    if classic:
        _start_chat_classic()
    else:
        _start_tui()


def _start_tui(model_override: str | None = None) -> None:
    """Launch the Textual full-screen interface."""
    try:
        from hex_cli.tui import run_tui
    except ImportError as e:
        ui.print_error(f"TUI dependencies missing: {e}")
        ui.print_info("Install with: pip install textual")
        ui.print_info("Falling back to classic mode\u2026")
        _start_chat_classic(model_override=model_override)
        return

    root = _project_root()
    load_dotenv_if_present(root)
    try:
        run_tui(project_root=root, model=model_override)
    except Exception as e:
        ui.print_error(f"TUI failed to start: {e}")
        ui.print_info("Try classic mode: hex --classic")
        raise typer.Exit(1)


def _start_chat_classic(model_override: str | None = None) -> None:
    """Classic Rich line-prompt session (pre-TUI)."""
    root = _project_root()
    load_dotenv_if_present(root)
    config = load_config()

    provider_cfg = config.get_active_provider()
    model = model_override or provider_cfg.default_model

    try:
        provider = create_provider(provider_cfg, model=model)
    except ValueError as e:
        ui.print_error(str(e))
        ui.print_info("Run `hex doctor` for diagnostics, or `hex init` to create config.")
        raise typer.Exit(1)

    permissions = _setup_permissions(config, root)

    ui.print_banner(
        project_path=str(root),
        provider=provider_cfg.name,
        model=model,
    )

    from hex_cli.agent.loop import AgentLoop

    agent = AgentLoop(root, provider, config, permissions)

    while True:
        user_input = ui.prompt_user()
        if not user_input:
            continue

        lower = user_input.lower().strip()
        if lower in ("/exit", "/quit", "exit", "quit"):
            ui.print_info("Goodbye.")
            break
        if lower in ("/help", "help"):
            ui.print_help()
            continue
        if lower == "/clear":
            agent.reset_context()
            continue
        if lower == "/status":
            _show_status(config, root, model)
            continue
        if lower.startswith("/model"):
            parts = user_input.split(maxsplit=1)
            if len(parts) == 2:
                model = parts[1].strip()
                try:
                    provider = create_provider(provider_cfg, model=model)
                    agent.provider = provider
                    ui.print_success(f"Model set to {model}")
                except Exception as e:
                    ui.print_error(str(e))
            else:
                ui.print_info(f"Current model: {model}")
            continue
        if lower.startswith("/provider"):
            parts = user_input.split(maxsplit=1)
            if len(parts) == 2:
                name = parts[1].strip()
                if name not in config.providers:
                    ui.print_error(f"Unknown provider. Available: {list(config.providers)}")
                    continue
                config.active_provider = name
                save_config(config)
                provider_cfg = config.get_active_provider()
                model = provider_cfg.default_model
                try:
                    provider = create_provider(provider_cfg, model=model)
                    agent.provider = provider
                    ui.print_success(f"Provider set to {name} (model {model})")
                except Exception as e:
                    ui.print_error(str(e))
            else:
                ui.print_info(f"Current provider: {config.active_provider}")
            continue
        if lower == "/permissions":
            perms = config.permissions
            ui.print_table(
                ["Action", "Mode"],
                [
                    ["read_files", perms.read_files],
                    ["create_files", perms.create_files],
                    ["modify_files", perms.modify_files],
                    ["delete_files", perms.delete_files],
                    ["run_commands", perms.run_commands],
                    ["git_commit", perms.git_commit],
                    ["git_push", perms.git_push],
                    ["deployment", perms.deployment],
                ],
                title="Permission settings",
            )
            continue

        try:
            agent.run(user_input)
        except KeyboardInterrupt:
            ui.print_warning("Interrupted.")
        except Exception as e:
            ui.print_error(f"Agent error: {e}")


def _show_status(config: AppConfig, root: Path, model: str) -> None:
    p = config.get_active_provider()
    key_set = bool(get_api_key(p))
    ui.print_table(
        ["Key", "Value"],
        [
            ["Project", str(root)],
            ["Provider", config.active_provider],
            ["Model", model],
            ["API key set", "yes" if key_set else "no"],
            ["Config", str(get_config_path())],
            ["Max steps", str(config.max_agent_steps)],
        ],
        title="HEX Status",
    )


@app.command()
def chat(
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model override"),
    classic: bool = typer.Option(
        False,
        "--classic",
        help="Use the classic line-oriented prompt instead of the full-screen TUI",
    ),
) -> None:
    """Start an interactive coding session (default: full-screen TUI)."""
    if classic:
        _start_chat_classic(model_override=model)
    else:
        _start_tui(model_override=model)


@app.command()
def doctor() -> None:
    """Diagnose environment, configuration, and provider connectivity."""
    root = _project_root()
    load_dotenv_if_present(root)
    config = load_config()
    cfg_path = get_config_path()

    ui.console.print(f"\n[bold accent]HEX Doctor[/bold accent]  v{__version__}\n")

    rows = []
    rows.append(["Python", f"{sys.version.split()[0]} ({sys.executable})"])
    rows.append(["Platform", f"{platform.system()} {platform.release()}"])
    rows.append(["CWD", str(root)])
    rows.append(["Config dir", str(get_config_dir())])
    rows.append(["Config file", f"{cfg_path} ({'exists' if cfg_path.exists() else 'missing'})"])

    git_path = shutil.which("git")
    rows.append(["Git", git_path or "not found"])

    rows.append(["Active provider", config.active_provider])
    p = config.get_active_provider()
    key = get_api_key(p)
    rows.append([f"API key ({p.api_key_env})", "set" if key else "NOT SET"])
    rows.append(["Base URL", p.base_url or "(default)"])
    rows.append(["Default model", p.default_model])

    ui.print_table(["Check", "Result"], rows)

    ui.console.print()
    if not key and p.name != "ollama":
        ui.print_warning(
            f"No API key found for {p.name}. Set {p.api_key_env} or add it to .env"
        )
        ui.print_info("Free / local options:")
        ui.print_info("  \u2022 Ollama (local): install from https://ollama.com then `ollama serve`")
        ui.print_info("  \u2022 Groq free tier: https://console.groq.com")
        ui.print_info("  \u2022 OpenRouter: https://openrouter.ai")
        return

    ui.print_info(f"Probing {p.name} \u2026")
    try:
        provider = create_provider(p)
        from hex_cli.providers.base import ChatMessage

        resp = provider.chat(
            [ChatMessage(role="user", content="Reply with exactly: pong")],
            tools=None,
        )
        content = (resp.content or "").strip()
        ui.print_success(f"Provider reachable. Response: {content[:80]!r}")
    except ProviderError as e:
        ui.print_error(str(e))
    except Exception as e:
        ui.print_error(f"Probe failed: {e}")


@app.command()
def config(
    show: bool = typer.Option(True, "--show/--edit", help="Show or interactively edit"),
) -> None:
    """View or edit HEX configuration."""
    cfg = load_config()
    path = get_config_path()

    if show:
        ui.console.print(f"\n[bold]Config file:[/bold] {path}\n")
        ui.console.print(cfg.model_dump_json(indent=2))
        return

    ui.print_info(f"Current provider: {cfg.active_provider}")
    providers = list(cfg.providers.keys())
    choice = Prompt.ask(
        "Select provider",
        choices=providers,
        default=cfg.active_provider,
    )
    cfg.active_provider = choice
    p = cfg.providers[choice]
    model = Prompt.ask("Default model", default=p.default_model)
    p.default_model = model
    save_config(cfg)
    ui.print_success(f"Saved. Provider={choice}, model={model}")


@app.command("models")
def models_cmd() -> None:
    """List models from the active provider (best-effort)."""
    load_dotenv_if_present(_project_root())
    cfg = load_config()
    p = cfg.get_active_provider()
    try:
        provider = create_provider(p)
        names = provider.list_models()
        if not names:
            ui.print_info(f"Default model: {p.default_model}")
            return
        ui.print_table(
            ["#", "Model"],
            [[str(i + 1), n] for i, n in enumerate(names[:50])],
            title=f"Models from {p.name}",
        )
    except Exception as e:
        ui.print_error(str(e))
        ui.print_info(f"Configured default: {p.default_model}")


@app.command()
def model(
    name: str = typer.Argument(..., help="Model identifier to set as default"),
) -> None:
    """Set the default model for the active provider."""
    cfg = load_config()
    p = cfg.get_active_provider()
    p.default_model = name
    save_config(cfg)
    ui.print_success(f"Default model for {cfg.active_provider} set to {name}")


@app.command()
def init() -> None:
    """Initialise ~/.hex configuration directory and default config."""
    ensure_config_dir()
    path = get_config_path()
    if path.exists():
        ui.print_warning(f"Config already exists at {path}")
        if not typer.confirm("Overwrite with defaults?"):
            raise typer.Exit(0)

    cfg = AppConfig()
    save_config(cfg)
    ui.print_success(f"Created {path}")
    ui.print_info("Set an API key, e.g.:")
    ui.print_info("  $env:OPENAI_API_KEY = 'sk-\u2026'     # PowerShell")
    ui.print_info("  export OPENAI_API_KEY=sk-\u2026       # bash")
    ui.print_info("Or create ~/.hex/.env with KEY=value lines.")
    ui.print_info("For local models: install Ollama, then `hex config` and select ollama.")


def run() -> None:
    app()


if __name__ == "__main__":
    run()
