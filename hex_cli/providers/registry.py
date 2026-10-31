"""Built-in provider registry for HEX CLI (Stage 2).

Defines supported integrations, default endpoints, and env var names.
Does not store secrets.
"""

from __future__ import annotations

from dataclasses import dataclass

from hex_cli.config import ProviderConfig


@dataclass(frozen=True)
class ProviderSpec:
    """Static description of a supported provider integration."""

    id: str
    display_name: str
    base_url: str
    api_key_env: str
    default_model: str
    requires_key: bool = True
    docs_url: str = ""
    notes: str = ""
    openai_compatible: bool = True


PROVIDER_SPECS: dict[str, ProviderSpec] = {
    "openrouter": ProviderSpec(
        id="openrouter",
        display_name="OpenRouter",
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY",
        default_model="openrouter/free",
        docs_url="https://openrouter.ai/keys",
        notes="Many models including free-tier :free routes",
    ),
    "openai": ProviderSpec(
        id="openai",
        display_name="OpenAI",
        base_url="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        default_model="gpt-4o-mini",
        docs_url="https://platform.openai.com/api-keys",
        notes="Paid API",
    ),
    "anthropic": ProviderSpec(
        id="anthropic",
        display_name="Anthropic",
        base_url="https://api.anthropic.com/v1",
        api_key_env="ANTHROPIC_API_KEY",
        default_model="claude-3-5-haiku-latest",
        docs_url="https://console.anthropic.com/",
        notes="OpenAI-compatible gateway if enabled; otherwise use OpenRouter",
    ),
    "google": ProviderSpec(
        id="google",
        display_name="Google Gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key_env="GOOGLE_API_KEY",
        default_model="gemini-2.0-flash",
        docs_url="https://aistudio.google.com/apikey",
        notes="Gemini via OpenAI-compatible endpoint",
    ),
    "groq": ProviderSpec(
        id="groq",
        display_name="Groq",
        base_url="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
        default_model="llama-3.3-70b-versatile",
        docs_url="https://console.groq.com/keys",
        notes="Fast inference; free tier with limits",
    ),
    "nvidia": ProviderSpec(
        id="nvidia",
        display_name="NVIDIA NIM",
        base_url="https://integrate.api.nvidia.com/v1",
        api_key_env="NVIDIA_API_KEY",
        default_model="meta/llama-3.1-8b-instruct",
        docs_url="https://build.nvidia.com/",
        notes="NVIDIA API catalog",
    ),
    "cerebras": ProviderSpec(
        id="cerebras",
        display_name="Cerebras",
        base_url="https://api.cerebras.ai/v1",
        api_key_env="CEREBRAS_API_KEY",
        default_model="llama3.1-8b",
        docs_url="https://inference.cerebras.ai/",
        notes="High-speed inference",
    ),
    "mistral": ProviderSpec(
        id="mistral",
        display_name="Mistral",
        base_url="https://api.mistral.ai/v1",
        api_key_env="MISTRAL_API_KEY",
        default_model="mistral-small-latest",
        docs_url="https://console.mistral.ai/",
        notes="Mistral cloud API",
    ),
    "ollama": ProviderSpec(
        id="ollama",
        display_name="Ollama (local)",
        base_url="http://localhost:11434/v1",
        api_key_env="OLLAMA_API_KEY",
        default_model="llama3.2",
        requires_key=False,
        docs_url="https://ollama.com",
        notes="Local models — no cloud key required",
    ),
    "custom": ProviderSpec(
        id="custom",
        display_name="Custom OpenAI-compatible",
        base_url="http://localhost:8000/v1",
        api_key_env="HEX_CUSTOM_API_KEY",
        default_model="default",
        requires_key=False,
        notes="Any OpenAI-compatible base URL",
    ),
}


def list_provider_specs() -> list[ProviderSpec]:
    return list(PROVIDER_SPECS.values())


def get_provider_spec(provider_id: str) -> ProviderSpec | None:
    return PROVIDER_SPECS.get(provider_id)


def spec_to_config(spec: ProviderSpec, *, base_url: str | None = None) -> ProviderConfig:
    return ProviderConfig(
        name=spec.id,
        base_url=base_url or spec.base_url,
        api_key_env=spec.api_key_env,
        default_model=spec.default_model,
    )


def ensure_default_providers(providers: dict[str, ProviderConfig]) -> dict[str, ProviderConfig]:
    """Merge missing built-in providers into an existing map (non-destructive)."""
    out = dict(providers)
    for pid, spec in PROVIDER_SPECS.items():
        if pid not in out:
            out[pid] = spec_to_config(spec)
    return out
