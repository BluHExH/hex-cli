"""Tests for configuration loading and defaults."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hex_cli.config import AppConfig, PermissionConfig, load_config, save_config


def test_default_config_has_providers():
    cfg = AppConfig()
    assert "openai" in cfg.providers
    assert "ollama" in cfg.providers
    assert cfg.active_provider == "openai"


def test_get_active_provider():
    cfg = AppConfig()
    p = cfg.get_active_provider()
    assert p.name == "openai"
    assert p.default_model


def test_unknown_provider_raises():
    cfg = AppConfig()
    cfg.active_provider = "nonexistent"
    with pytest.raises(ValueError):
        cfg.get_active_provider()


def test_save_and_load(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("hex_cli.config.get_config_dir", lambda: tmp_path)
    monkeypatch.setattr("hex_cli.config.get_config_path", lambda: tmp_path / "config.json")

    cfg = AppConfig(active_provider="ollama", max_agent_steps=10)
    save_config(cfg)
    assert (tmp_path / "config.json").exists()

    loaded = load_config()
    assert loaded.active_provider == "ollama"
    assert loaded.max_agent_steps == 10


def test_permission_defaults():
    p = PermissionConfig()
    assert p.read_files == "allow"
    assert p.create_files == "ask"
    assert p.git_push == "ask"


def test_corrupt_config_falls_back(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("hex_cli.config.get_config_dir", lambda: tmp_path)
    path = tmp_path / "config.json"
    path.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr("hex_cli.config.get_config_path", lambda: path)
    cfg = load_config()
    assert isinstance(cfg, AppConfig)
    assert cfg.active_provider == "openai"
