from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class HexSettings:
    workspace: str = "."
    provider: str = "mock"
    model: str = "mock-smart"
    api_base: str = ""
    permission_mode: str = "prompt"  # prompt | allow | deny
    max_tool_rounds: int = 8
    context_max_chars: int = 120_000
    theme: str = "hex-dark"

    def api_key(self) -> str:
        return (
            os.environ.get("HEX_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("OPENROUTER_API_KEY")
            or ""
        )


def _config_path(workspace: Path) -> Path:
    return workspace / ".hex" / "config.json"


def load_settings(workspace: Path | None = None) -> HexSettings:
    root = (workspace or Path.cwd()).resolve()
    path = _config_path(root)
    data: dict[str, Any] = {}
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    settings = HexSettings(
        workspace=str(root),
        provider=str(data.get("provider", "mock")),
        model=str(data.get("model", "mock-smart")),
        api_base=str(data.get("api_base", "")),
        permission_mode=str(data.get("permission_mode", "prompt")),
        max_tool_rounds=int(data.get("max_tool_rounds", 8)),
        context_max_chars=int(data.get("context_max_chars", 120_000)),
        theme=str(data.get("theme", "hex-dark")),
    )
    return settings


def save_settings(settings: HexSettings) -> None:
    root = Path(settings.workspace).resolve()
    path = _config_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(settings)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
