"""Model catalog for HEX CLI (Stage 2).

Discovers models from provider APIs when possible. Free-model detection is
conservative: only models explicitly marked free by the provider (e.g.
OpenRouter `:free` suffix or zero pricing) are labeled free.
Never""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import httpx

from hex_cli.config import ProviderConfig
from hex_cli.providers.credentials import resolve_api_key
from hex_cli.providers.registry import get_provider_spec

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
        ctx = f" \u00b7 {self.context_length // 1000}k" if self.context_length else ""
        tools = " \u00b7 tools" if self.supports_tools else ""
        return f"[{tier}] {self.id}{ctx}{tools}"


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
        return "free"
    if mid.endswith(":free") or ":free" in mid:
        return "free"
    return "unknown"


def fetch_openrouter_models(timeout: float = 20.0) -> list[ModelInfo]:
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
        ctx = item.get("context_length") or (item.get("top_provider") or {}).get("context_length")
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
                description=str(item.get("description") or "")[:200],
                raw=item,
            )
        )
    return out


def fetch_openai_compatible_models(config: ProviderConfig, *, timeout: float = 20.0) -> list[ModelInfo]:
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
            mid, meta = item, {}
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
                cost_tier=classify_generic(mid, config.name),
                raw=meta,
            )
        )
    return out


def fallback_models_for(provider_id: str) -> list[ModelInfo]:
    if provider_id == "openrouter":
        return [
            ModelInfo(
                id=mid,
                name=mid,
                provider="openrouter",
                cost_tier="free",
                description="OpenRouter free-route fallback",
            )
            for mid in OPENROUTER_FREE_FALLBACK
        ]
    if provider_id == "ollama":
        return [
            ModelInfo(id="llama3.2", name="llama3.2", provider="ollama", cost_tier="free"),
            ModelInfo(id="qwen2.5-coder", name="qwen2.5-coder", provider="ollama", cost_tier="free"),
        ]
    spec = get_provider_spec(provider_id)
    if spec:
        return [
            ModelInfo(
                id=spec.default_model,
                name=spec.default_model,
                provider=provider_id,
                cost_tier="unknown",
            )
        ]
    return []


def discover_models(
    config: ProviderConfig,
    *,
    free_only: bool = False,
    query: str = "",
) -> tuple[list[ModelInfo], str | None]:
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
            m for m in models
            if q in m.id.lower() or q in m.name.lower() or q in m.provider.lower()
        ]
    models.sort(key=lambda m: (0 if m.cost_tier == "free" else 1, m.id.lower()))
    return models, error


def free_models_catalog() -> list[ModelInfo]:
    try:
        models = fetch_openrouter_models()
        free = [m for m in models if m.cost_tier == "free"]
        if free:
            return free
    except Exception:
        pass
    return fallback_models_for("openrouter") + fallback_models_for("ollama")
