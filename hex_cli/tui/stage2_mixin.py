"""Stage 2 TUI actions mixed into HexApp."""

from __future__ import annotations

from typing import Any

from hex_cli.config import get_api_key, save_config
from hex_cli.providers.base import create_provider
from hex_cli.providers.catalog import discover_models, free_models_catalog
from hex_cli.providers.credentials import (
    delete_credential,
    list_connected_provider_ids,
    mask_key,
    set_credential,
)
from hex_cli.providers.registry import get_provider_spec, list_provider_specs, spec_to_config
from hex_cli.tui.widgets.dialogs import SelectDialog
from hex_cli.tui.widgets.provider_dialogs import (
    ConnectProviderDialog,
    ModelBrowserDialog,
    ProvidersStatusDialog,
    SettingsDialog,
)


class Stage2Mixin:
    """Provider/model management actions for HexApp."""

    def _show_onboarding(self) -> None:
        specs = list_provider_specs()
        lines = [
            "Welcome to HEX — AI coding agent.",
            "",
            "No API key is configured yet. You can still explore the interface.",
            "",
            "Connect a provider:",
            "  /connect          interactive provider + API key setup",
            "  /models           browse models (free filter available)",
            "  /providers        list connected providers",
            "",
            "Popular options:",
        ]
        for s in specs[:6]:
            lines.append(f"  • {s.display_name}  ({s.api_key_env})")
        lines.extend(
            [
                "",
                "Free routes: use OpenRouter models ending in :free, or Ollama locally.",
                "Type /help for all commands.",
            ]
        )
        self._post_system("\n".join(lines))

    def action_pick_model(self) -> None:
        self._post_status("Loading model catalog…")
        self.run_worker(self._load_and_show_models, exclusive=True, thread=True)

    def _load_and_show_models(self) -> None:
        try:
            pcfg = self.config.get_active_provider()
            models, err = discover_models(pcfg)
            if err:
                self.call_from_thread(
                    self._post_status, f"Catalog warning: {err} (using fallbacks)"
                )
            if not models:
                models = free_models_catalog()
        except Exception as e:
            self.call_from_thread(self._post_error, f"Model discovery failed: {e}")
            models = free_models_catalog()

        def _done(choice: str | None) -> None:
            if choice:
                self._set_model(choice)

        def _open() -> None:
            self.push_screen(
                ModelBrowserDialog(
                    models,
                    current=self.state.model,
                    title=f"Models — {self.state.provider_name}",
                ),
                _done,
            )

        self.call_from_thread(_open)

    def action_connect_provider(self) -> None:
        specs = list_provider_specs()
        connected = set(list_connected_provider_ids())

        def _done(result: tuple[str, str] | None) -> None:
            if not result:
                return
            pid, key = result
            try:
                if key:
                    set_credential(pid, key)
                self.config.active_provider = pid
                if pid not in self.config.providers:
                    spec = get_provider_spec(pid)
                    if spec:
                        self.config.providers[pid] = spec_to_config(spec)
                pcfg = self.config.providers[pid]
                if key:
                    import os
                    os.environ[pcfg.api_key_env] = key
                model = self.config.selected_model or pcfg.default_model
                self._provider = create_provider(pcfg, model=model, require_key=False)
                self.state.provider_name = pid
                self.state.model = model
                self.state.connected = bool(get_api_key(pcfg)) or pid in ("ollama", "custom")
                save_config(self.config)
                if self.state.connected:
                    self._setup_agent()
                    self.state.status_message = "Ready"
                    self._post_system(
                        f"Connected to {pid}. Model: {model}. "
                        f"Key: {mask_key(key or get_api_key(pcfg))}. "
                        "Type /models to browse models."
                    )
                else:
                    self._post_status(
                        f"Provider {pid} selected but no key available. "
                        "Re-run /connect with a key."
                    )
            except Exception as e:
                self._post_error(f"Connect failed: {e}")
            self._refresh_chrome()

        self.push_screen(ConnectProviderDialog(specs, connected), _done)

    def action_show_providers(self) -> None:
        lines = []
        for pid, pcfg in self.config.providers.items():
            key = get_api_key(pcfg)
            status = "connected" if key or pid in ("ollama", "custom") else "no key"
            active = " (active)" if pid == self.config.active_provider else ""
            lines.append(f"• {pid}{active} — {status} — key {mask_key(key)}")
        stored = list_connected_provider_ids()
        if stored:
            lines.append("")
            lines.append("Stored credentials: " + ", ".join(stored))
        self.push_screen(ProvidersStatusDialog(lines))

    def action_disconnect_provider(self) -> None:
        self._disconnect_named(self.state.provider_name)

    def _disconnect_named(self, name: str) -> None:
        deleted = delete_credential(name)
        if deleted:
            self._post_system(f"Removed stored key for {name}.")
        else:
            self._post_status(f"No stored key for {name} (env vars are not cleared).")
        try:
            pcfg = self.config.get_active_provider()
            key = get_api_key(pcfg)
            self.state.connected = bool(key) or pcfg.name in ("ollama", "custom")
            if not self.state.connected:
                self._agent = None
                self.state.status_message = "Not connected"
        except Exception:
            pass
        self._refresh_chrome()

    def action_show_settings(self) -> None:
        text = (
            f"Active provider: {self.config.active_provider}\n"
            f"Model: {self.state.model}\n"
            f"Selected model (saved): {self.config.selected_model or '—'}\n"
            f"Project: {self.project_root}\n"
            f"Config dir: uses ~/.hex/\n"
            f"Credentials: ~/.hex/credentials.json\n"
            f"Max agent steps: {self.config.max_agent_steps}\n"
            f"Connected: {self.state.connected}\n"
        )
        self.push_screen(SettingsDialog(text))

    def _set_model(self, model: str) -> None:
        try:
            pcfg = self.config.get_active_provider()
            self._provider = create_provider(pcfg, model=model, require_key=False)
            self.state.model = model
            pcfg.default_model = model
            self.config.selected_model = model
            save_config(self.config)
            if self.state.connected:
                if self._agent:
                    self._agent.provider = self._provider
                else:
                    self._setup_agent()
            self._post_system(f"Model set to {model}")
        except Exception as e:
            self._post_error(str(e))
        self._refresh_chrome()

    def _set_provider(self, name: str) -> None:
        if name not in self.config.providers:
            self._post_error(f"Unknown provider: {name}. Use /connect to add one.")
            return
        try:
            self.config.active_provider = name
            save_config(self.config)
            pcfg = self.config.get_active_provider()
            model = self.config.selected_model or pcfg.default_model
            self._provider = create_provider(pcfg, model=model, require_key=False)
            self.state.provider_name = name
            self.state.model = model
            key = get_api_key(pcfg)
            self.state.connected = bool(key) or name in ("ollama", "custom")
            if self.state.connected:
                self._setup_agent()
                self.state.status_message = "Ready"
                self._post_system(f"Provider set to {name} (model {model})")
            else:
                self._agent = None
                self.state.status_message = "Not connected"
                self._post_status(f"Switched to {name} but no API key. Run /connect.")
        except Exception as e:
            self._post_error(str(e))
            self.state.connected = False
        self._refresh_chrome()
