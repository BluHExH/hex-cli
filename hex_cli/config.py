"""Configuration management for HEX CLI.

User-level config lives in ~/.hex/ (or %USERPROFILE%\\.hex on Windows).
API keys are read from environment variables or a local .env file —
never stored in tracked project files.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_config_dir() -> Path:
    """Return the user-level HEX config directory."""
    home = Path.home()
    return home / ".hex"


def get_config_path() -> Path:
    return get_config_dir() / "config.json"


def get_history_path() -> Path:
    return get_config_dir() / "history.jsonl"


PermissionMode = Literal["allow", "ask", "deny"]


class PermissionConfig(BaseModel):
    """Controls how the agent handles potentially risky operations."""

    read_files: PermissionMode = "allow"
    create_files: PermissionMode = "ask"
    modify_files: PermissionMode = "ask"
    delete_files: PermissionMode = "ask"
    run_commands: PermissionMode = "ask"
    git_commit: PermissionMode = "ask"
    git_push: PermissionMode = "ask"
    deployment: PermissionMode = "ask"


class ProviderConfig(BaseModel):
    """Settings for a single LLM provider."""

    name: str = "openai"
    base_url: str | None = None
    api_key_env: str = "OPENAI_API_KEY"
    default_model: str = "gpt-4o-mini"
    timeout_seconds: float = 120.0
    max_retries: int = 2


class AppConfig(BaseModel):
    """Top-level HEX CLI configuration."""

    version: str = "0.1.0"
    active_provider: str = "openai"
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    permissions: PermissionConfig = Field(default_factory=PermissionConfig)
    max_agent_steps: int = 25
    max_file_size_bytes: int = 512_000
    max_command_output_chars: int = 30_000
    command_timeout_seconds: float = 60.0
    context_max_files: int = 40
    context_max_chars: int = 80_000
    session_history: bool = True

    def model_post_init(self, __context: Any) -> None:
        if not self.providers:
            self.providers = {
                "openai": ProviderConfig(
                    name="openai",
                    base_url="https://api.openai.com/v1",
                    api_key_env="OPENAI_API_KEY",
                    default_model="gpt-4o-mini",
                ),
                "ollama": ProviderConfig(
                    name="ollama",
                    base_url="http://localhost:11434/v1",
                    api_key_env="OLLAMA_API_KEY",
                    default_model="llama3.2",
                ),
                "openrouter": ProviderConfig(
                    name="openrouter",
                    base_url="https://openrouter.ai/api/v1",
                    api_key_env="OPENROUTER_API_KEY",
                    default_model="openai/gpt-4o-mini",
                ),
                "groq": ProviderConfig(
                    name="groq",
                    base_url="https://api.groq.com/openai/v1",
                    api_key_env="GROQ_API_KEY",
                    default_model="llama-3.3-70b-versatile",
                ),
            }

    def get_active_provider(self) -> ProviderConfig:
        if self.active_provider not in self.providers:
            raise ValueError(
                f"Unknown provider '{self.active_provider}'. "
                f"Available: {list(self.providers.keys())}"
            )
        return self.providers[self.active_provider]


def ensure_config_dir() -> Path:
    cfg_dir = get_config_dir()
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir


def load_config() -> AppConfig:
    """Load config from disk, creating defaults if missing."""
    path = get_config_path()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return AppConfig.model_validate(data)
        except Exception:
            return AppConfig()
    return AppConfig()


def save_config(config: AppConfig) -> None:
    ensure_config_dir()
    path = get_config_path()
    path.write_text(
        config.model_dump_json(indent=2),
        encoding="utf-8",
    )


def load_dotenv_if_present(project_root: Path | None = None) -> None:
    """Load .env from project root or cwd without overriding existing env vars."""
    from dotenv import load_dotenv

    candidates = []
    if project_root:
        candidates.append(project_root / ".env")
    candidates.append(Path.cwd() / ".env")
    candidates.append(get_config_dir() / ".env")

    for p in candidates:
        if p.is_file():
            load_dotenv(p, override=False)
            break


def get_api_key(provider: ProviderConfig) -> str | None:
    """Return the API key for a provider from the environment. Never log it."""
    key = os.environ.get(provider.api_key_env)
    if key:
        return key.strip()
    if provider.name == "ollama":
        return os.environ.get("OLLAMA_API_KEY", "ollama")
    return None


class EnvInfo(BaseModel):
    python_version: str
    platform: str
    config_dir: str
    config_exists: bool
    active_provider: str
    api_key_set: bool
    git_available: bool
    ollama_reachable: bool | None = None
