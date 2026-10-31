"""Model catalog for HEX CLI (Stage 2).

Discovers models from provider APIs when possible. Free-model detection is
conservative: only models explicitly marked free by the provider (e.g.
OpenRouter `:free` suffix or `pricing.prompt == 0`) are labeled free.
Never invent pricing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import httpx

from hex_cli.config import ProviderConfig
from hex_cli.providers.credentials import resolve_api_key
from hex_cli.providers.registry import PROVIDER_SPECS, get_provider_spec

CostTier = Literal["free", "paid", "unknown"]


@dataclass
class ModelInfo:
    id: str
    name: str
    provider: str
    context_length: int | None = None
    cost_tier: CostTier = "unknown"
    supports_tools: bool | None = None
    description: str = ""
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    def label(self) -> str:
        tier = {"free": "FREE", "paid": "PAID", "unknown": "?"}.get(self.cost_tier, "?")
        ctx = f" · {self.context_length // 1000}k" if self.context_length else ""
        tools = " · tools" if self.supports_tools else ""
        return f"[{tier}] {self.id}{ctx}{tools}"


# Curated fallback free routes (OpenRouter official :free suffix convention).
# These are only used as static fallbacks when the live catalog cannot be fetched.
# All entries use the OpenRouter `:free` naming convention.
OPENROUTER_FREE_FALLBACK: list[str] = [
    "openrouter/free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "google/gemma-3-27b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "qwen/qwen3-14b:free",
]


def classify_openrouter_model(item: dict[str, Any]) -> CostTier:
    mid = str(item.get("id") or "")
    if mid.endswith(":free") or ":free" in mid:
        return "free"
    pricing = item.get("pricing") or {}
    try:
        prompt = float(pricing.get("prompt") or 0)
        completion = float(pricing.get("completion") or 0)
        if prompt == 0 and completion == 0:
            return "free"
        if prompt > 0 or completion > 0:
            return "paid"
    except (TypeError, ValueError):
        pass
    return "unknown"


def classify_generic(model_id: str, provider: str) -> CostTier:
    mid = model_id.lower()
    if provider == "ollama":
        return "free"  # local inference — no cloud billing from HEX's perspective
    if mid.endswith(":free") or ":free" in mid:
        return "free"
    # Do not guess — unknown is safer than mislabeling paid as free
    return "unknown"


def fetch_openrouter_models(timeout: float = 20.0) -> list[ModelInfo]:
    """Fetch model list from OpenRouter public models API (key optional for listing)."""
    url = "https://openrouter.ai/api/v1/models"
    headers = {"User-Agent": "HEX-CLI/0.3"}
    with httpx.Client(timeout=timeout) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    items = data.get("data") or data.get("models") or []
    out: list[ModelInfo] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        mid = str(item.get("id") or "")
        if not mid:
            continue
        ctx = item.get("context_length") or item.get("top_provider", {}).get("context_length")
        try:
            ctx_i = int(ctx) if ctx is not None else None
        except (TypeError, ValueError):
            ctx_i = None
        out.append(
            ModelInfo(
                id=mid,
                name=str(item.get("name") or mid),
                provider="openrouter",
                context_length=ctx_i,
                cost_tier=classify_openrouter_model(item),
                supports_tools=None,
                description=str(item.get("description") or "")[:200],
                raw=item,
            )
        )
    return out


def fetch_openai_compatible_models(
    config: ProviderConfig,
    *,
    timeout: float = 20.0,
) -> list[ModelInfo]:
    """GET {base_url}/models using resolved credentials."""
    base = (config.base_url or "").rstrip("/")
    if not base:
        return []
    key = resolve_api_key(config)
    headers = {"User-Agent": "HEX-CLI/0.3"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    url = f"{base}/models"
    with httpx.Client(timeout=timeout) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    items = data.get("data") or data.get("models") or []
    out: list[ModelInfo] = []
    for item in items:
        if isinstance(item, str):
            mid = item
            meta: dict[str, Any] = {}
        elif isinstance(item, dict):
            mid = str(item.get("id") or item.get("name") or "")
            meta = item
        else:
            continue
        if not mid:
            continue
        out.append(
            ModelInfo(
                id=mid,
                name=mid,
                provider=config.name,
                context_length=None,
                cost_tier=classify_generic(mid, config.name),
                supports_tools=None,
                raw=meta,
            )
        )
    return out


def fallback_models_for(provider_id: str) -> list[ModelInfo]:
    """Static fallback when live discovery fails — only honest free labels."""
    if provider_id == "openrouter":
        return [
            ModelInfo(
                id=mid,
                name=mid,
                provider="openrouter",
                cost_tier="free",
                description="OpenRouter free-route fallback (verify at openrouter.ai/models)",
            )
            for mid in OPENROUTER_FREE_FALLBACK
        ]
    if provider_id == "ollama":
        return [
            ModelInfo(
                id="llama3.2",
                name="llama3.2",
                provider="ollama",
                cost_tier="free",
                description="Local Ollama model (pull required)",
            ),
            ModelInfo(
                id="qwen2.5-coder",
                name="qwen2.5-coder",
                provider="ollama",
                cost_tier="free",
            ),
        ]
    spec = get_provider_spec(provider_id)
    if spec:
        return [
            ModelInfo(
                id=spec.default_model,
                name=spec.default_model,
                provider=provider_id,
                cost_tier="unknown",
                description="Default model (live catalog unavailable)",
            )
        ]
    return []


def discover_models(
    config: ProviderConfig,
    *,
    free_only: bool = False,
    query: str = "",
) -> tuple[list[ModelInfo], str | None]:
    """Discover models for a provider. Returns (models, error_message)."""
    error: str | None = None
    models: list[ModelInfo] = []
    try:
        if config.name == "openrouter":
            models = fetch_openrouter_models()
        else:
            models = fetch_openai_compatible_models(config)
    except Exception as e:
        error = str(e)[:200]
        models = fallback_models_for(config.name)

    if not models:
        models = fallback_models_for(config.name)

    if free_only:
        models = [m for m in models if m.cost_tier == "free"]

    q = query.strip().lower()
    if q:
        models = [
            m
            for m in models
            if q in m.id.lower() or q in m.name.lower() or q in m.provider.lower()
        ]

    # Stable sort: free first, then by id
    models.sort(key=lambda m: (0 if m.cost_tier == "free" else 1, m.id.lower()))
    return models, error


def free_models_catalog() -> list[ModelInfo]:
    """Best-effort free model list (OpenRouter live + fallbacks)."""
    try:
        models = fetch_openrouter_models()
        free = [m for m in models if m.cost_tier == "free"]
        if free:
            return free
    except Exception:
        pass
    return fallback_models_for("openrouter") + fallback_models_for("ollama")
