"""Stage 2: provider registry, credentials, catalog, free-model labeling."""

from __future__ import annotations

from pathlib import Path

import pytest

from hex_cli.config import AppConfig, ProviderConfig
from hex_cli.providers.catalog import (
    classify_generic,
    classify_openrouter_model,
    fallback_models_for,
    free_models_catalog,
)
from hex_cli.providers.credentials import (
    delete_credential,
    get_stored_credential,
    list_connected_provider_ids,
    mask_key,
    resolve_api_key,
    set_credential,
)
from hex_cli.providers.registry import (
    PROVIDER_SPECS,
    ensure_default_providers,
    list_provider_specs,
)


def test_provider_specs_include_core() -> None:
    ids = {s.id for s in list_provider_specs()}
    for required in (
        "openrouter",
        "openai",
        "google",
        "groq",
        "nvidia",
        "cerebras",
        "mistral",
        "anthropic",
        "ollama",
        "custom",
    ):
        assert required in ids
        assert required in PROVIDER_SPECS


def test_ensure_default_providers_merges() -> None:
    base = {"openai": ProviderConfig(name="openai")}
    merged = ensure_default_providers(base)
    assert "openai" in merged
    assert "openrouter" in merged
    assert "ollama" in merged


def test_credentials_store_and_mask(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr("hex_cli.config.get_config_dir", lambda: tmp_path / ".hex")
    monkeypatch.setattr(
        "hex_cli.providers.credentials.get_config_dir", lambda: tmp_path / ".hex"
    )

    assert get_stored_credential("openrouter") is None
    set_credential("openrouter", "sk-test-abcdef123456")
    assert get_stored_credential("openrouter") == "sk-test-abcdef123456"
    assert "openrouter" in list_connected_provider_ids()
    masked = mask_key("sk-test-abcdef123456")
    assert "abcdef123456" not in masked or "\u2026" in masked
    assert delete_credential("openrouter") is True
    assert get_stored_credential("openrouter") is None

    with pytest.raises(ValueError):
        set_credential("x", "  ")


def test_resolve_api_key_prefers_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg_dir = tmp_path / ".hex"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("hex_cli.providers.credentials.get_config_dir", lambda: cfg_dir)
    monkeypatch.setattr("hex_cli.config.get_config_dir", lambda: cfg_dir)
    cfg = ProviderConfig(name="groq", api_key_env="GROQ_API_KEY")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    set_credential("groq", "stored-key-value-xx")
    monkeypatch.setenv("GROQ_API_KEY", "env-key-value-yy")
    assert resolve_api_key(cfg) == "env-key-value-yy"
    monkeypatch.delenv("GROQ_API_KEY")
    assert resolve_api_key(cfg) == "stored-key-value-xx"


def test_classify_openrouter_free_suffix() -> None:
    assert classify_openrouter_model({"id": "foo/bar:free"}) == "free"
    assert (
        classify_openrouter_model(
            {"id": "paid/model", "pricing": {"prompt": "0.001", "completion": "0.002"}}
        )
        == "paid"
    )
    assert (
        classify_openrouter_model(
            {"id": "zero", "pricing": {"prompt": "0", "completion": "0"}}
        )
        == "free"
    )


def test_classify_generic_never_guesses_paid_as_free() -> None:
    assert classify_generic("gpt-4o", "openai") == "unknown"
    assert classify_generic("llama3.2", "ollama") == "free"
    assert classify_generic("x:free", "openrouter") == "free"


def test_fallback_models_openrouter_are_free() -> None:
    models = fallback_models_for("openrouter")
    assert models
    assert all(m.cost_tier == "free" for m in models)
    assert all(":free" in m.id or m.id == "openrouter/free" for m in models)


def test_free_models_catalog_nonempty() -> None:
    models = free_models_catalog()
    assert isinstance(models, list)
    assert len(models) >= 1
    for m in models:
        assert m.cost_tier == "free"


def test_appconfig_defaults_include_providers() -> None:
    cfg = AppConfig()
    assert "openrouter" in cfg.providers
    assert "google" in cfg.providers
    assert cfg.active_provider in cfg.providers


def test_create_provider_without_key() -> None:
    from hex_cli.providers.base import create_provider

    cfg = ProviderConfig(
        name="openrouter",
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY_MISSING_XYZ",
        default_model="openrouter/free",
    )
    p = create_provider(cfg, require_key=False)
    assert p.model == "openrouter/free"
