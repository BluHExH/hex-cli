from __future__ import annotations

import json
from typing import Any, Iterator

import httpx

from hex_cli.providers.base import ChatMessage, ProviderResponse, ToolCall


class OpenAICompatProvider:
    """Minimal OpenAI-compatible Chat Completions client."""

    name = "openai_compat"

    def __init__(self, api_key: str, model: str, api_base: str = "https://api.openai.com/v1") -> None:
        self.api_key = api_key
        self.model = model
        self.api_base = api_base.rstrip("/")

    def complete(self, messages: list[ChatMessage], tools: list[dict[str, Any]] | None = None) -> ProviderResponse:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "parameters": {"type": "object", "properties": {k: {"type": "string"} for k in t.get("parameters", {})}},
                    },
                }
                for t in tools
            ]
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        with httpx.Client(timeout=120.0) as client:
            r = client.post(f"{self.api_base}/chat/completions", headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
        choice = data["choices"][0]["message"]
        content = choice.get("content") or ""
        tool_calls: list[ToolCall] = []
        for tc in choice.get("tool_calls") or []:
            fn = tc.get("function") or {}
            args_raw = fn.get("arguments") or "{}"
            try:
                args = json.loads(args_raw)
            except json.JSONDecodeError:
                args = {"raw": args_raw}
            tool_calls.append(ToolCall(id=tc.get("id", "call"), name=fn.get("name", ""), arguments=args))
        return ProviderResponse(content=content, tool_calls=tool_calls, raw=data)

    def stream_text(self, messages: list[ChatMessage]) -> Iterator[str]:
        # Fallback non-stream chunking for simplicity
        text = self.complete(messages).content
        step = max(1, len(text) // 20)
        for i in range(0, len(text), step):
            yield text[i : i + step]
