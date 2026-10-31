"""Secure-ish credential storage for HEX CLI (Windows-friendly).

Keys are stored in ~/.hex/credentials.json with restrictive file permissions.
Values are never written to logs by this module. Prefer environment variables
when set — they override stored credentials.
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

from hex_cli.config import ProviderConfig, ensure_config_dir, get_config_dir


def get_credentials_path() -> Path:
    return get_config_dir() / "credentials.json"


def _load_raw() -> dict[str, Any]:
    path = get_credentials_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_raw(data: dict[str, Any]) -> None:
    ensure_config_dir()
    path = get_credentials_path()
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    try:
        # Best-effort: owner read/write only (Unix). On Windows this may be a no-op.
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass


def set_credential(provider_id: str, api_key: str) -> None:
    """Store an API key for a provider id. Never log the key."""
    key = (api_key or "").strip()
    if not key:
        raise ValueError("API key cannot be empty")
    ensure_config_dir()
    data = _load_raw()
    providers = data.setdefault("providers", {})
    providers[provider_id] = {"api_key": key}
    _save_raw(data)
    # Also export into current process so the provider client sees it immediately
    # without requiring a restart — uses the provider's conventional env name when known.


def delete_credential(provider_id: str) -> bool:
    data = _load_raw()
    providers = data.get("providers") or {}
    if provider_id not in providers:
        return False
    del providers[provider_id]
    data["providers"] = providers
    _save_raw(data)
    return True


def get_stored_credential(provider_id: str) -> str | None:
    data = _load_raw()
    providers = data.get("providers") or {}
    entry = providers.get(provider_id) or {}
    key = entry.get("api_key")
    if isinstance(key, str) and key.strip():
        return key.strip()
    return None


def list_connected_provider_ids() -> list[str]:
    data = _load_raw()
    providers = data.get("providers") or {}
    return sorted(providers.keys())


def resolve_api_key(provider: ProviderConfig) -> str | None:
    """Resolve API key: environment first, then stored credential, then ollama default."""
    env_key = os.environ.get(provider.api_key_env)
    if env_key and env_key.strip():
        return env_key.strip()
    stored = get_stored_credential(provider.name)
    if stored:
        return stored
    if provider.name == "ollama":
        return os.environ.get("OLLAMA_API_KEY", "ollama")
    return None


def mask_key(key: str | None) -> str:
    """Return a safe display form of a key (never full secret)."""
    if not key:
        return "(not set)"
    k = key.strip()
    if len(k) <= 8:
        return "****"
    return k[:4] + "…" + k[-4:]
