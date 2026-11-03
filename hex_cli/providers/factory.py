from __future__ import annotations

from hex_cli.config.settings import HexSettings
from hex_cli.providers.base import Provider
from hex_cli.providers.mock import MockProvider
from hex_cli.providers.openai_compat import OpenAICompatProvider


def create_provider(settings: HexSettings) -> Provider:
    if settings.provider in {"mock", "offline", ""}:
        return MockProvider(model=settings.model)
    key = settings.api_key()
    base = settings.api_base or "https://api.openai.com/v1"
    if not key:
        return MockProvider(model=settings.model)
    return OpenAICompatProvider(api_key=key, model=settings.model, api_base=base)
