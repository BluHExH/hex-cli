"""OpenAI-compatible provider abstraction.

Supports OpenAI, Ollama, OpenRouter, Groq, and any endpoint that
speaks the OpenAI chat-completions + tools API.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable

import httpx
try:
    from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError
except ImportError:  # pragma: no cover
    APIConnectionError = APIStatusError = APITimeoutError = RateLimitError = Exception  # type: ignore
    OpenAI = None  # type: ignore

from hex_cli.config import ProviderConfig, get_api_key


@dataclass
class ChatMessage:
    role: str  # system | user | assistant | tool
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"role": self.role}
        if self.content is not None:
            d["content"] = self.content
        if self.tool_calls is not None:
            d["tool_calls"] = self.tool_calls
        if self.tool_call_id is not None:
            d["tool_call_id"] = self.tool_call_id
        if self.name is not None:
            d["name"] = self.name
        return d


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ProviderResponse:
    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: dict[str, Any] | None = None
    finish_reason: str | None = None


# Tool schemas exposed to the model
def _load_tool_schemas() -> list[dict[str, Any]]:
    try:
        from hex_cli.tools.registry import openai_tool_schemas
        return openai_tool_schemas()
    except Exception:
        return []

TOOL_SCHEMAS: list[dict[str, Any]] = _load_tool_schemas()


class BaseProvider:
    """Thin wrapper around the OpenAI-compatible Chat Completions API."""

    def __init__(
        self,
        config: ProviderConfig,
        model: str | None = None,
        *,
        require_key: bool = True,
    ):
        self.config = config
        self.model = model or config.default_model
        api_key = get_api_key(config)
        self._has_key = bool(api_key) or config.name in ("ollama", "custom")
        if require_key and not self._has_key:
            raise ValueError(
                f"API key not found. Use /connect in the TUI, set {config.api_key_env}, "
                "or add it to ~/.hex/credentials.json. See `hex doctor`."
            )
        if OpenAI is None:
            raise ImportError('openai package is required for LLM providers')
        self._client = OpenAI(
            api_key=api_key or "ollama",
            base_url=config.base_url,
            timeout=config.timeout_seconds,
            max_retries=config.max_retries,
        )

    def chat(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
    ) -> ProviderResponse:
        """Send a chat completion request with optional tools."""
        payload_messages = [m.to_dict() for m in messages]
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": payload_messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        last_error: Exception | None = None
        for attempt in range(self.config.max_retries + 1):
            try:
                response = self._client.chat.completions.create(**kwargs)
                return self._parse_response(response)
            except RateLimitError as e:
                last_error = e
                wait = 2 ** attempt
                time.sleep(wait)
            except APITimeoutError as e:
                last_error = e
                if attempt < self.config.max_retries:
                    time.sleep(1)
                else:
                    raise ProviderError(
                        f"Request timed out after {self.config.timeout_seconds}s. "
                        "Try increasing the timeout in config or using a faster model."
                    ) from e
            except APIConnectionError as e:
                raise ProviderError(
                    f"Cannot reach provider at {self.config.base_url}. "
                    "Check your network or that Ollama is running (if using local models)."
                ) from e
            except APIStatusError as e:
                status = e.status_code
                body = ""
                try:
                    body = e.response.text[:300]
                except Exception:
                    pass
                if status == 401:
                    raise ProviderError(
                        f"Authentication failed (401). Check that {self.config.api_key_env} "
                        "is set to a valid key."
                    ) from e
                if status == 403:
                    raise ProviderError(
                        "Access forbidden (403). Your key may lack permission for this model."
                    ) from e
                if status == 404:
                    raise ProviderError(
                        f"Model or endpoint not found (404). Model={self.model!r}, "
                        f"base_url={self.config.base_url}"
                    ) from e
                if status == 429:
                    last_error = e
                    time.sleep(2 ** attempt)
                    continue
                raise ProviderError(f"Provider error {status}: {body}") from e
            except Exception as e:
                raise ProviderError(f"Unexpected provider error: {e}") from e

        raise ProviderError(f"Rate limited after retries: {last_error}")

    def _parse_response(self, response: Any) -> ProviderResponse:
        choice = response.choices[0]
        msg = choice.message
        content = msg.content
        tool_calls: list[ToolCall] = []
        if getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {"_raw": tc.function.arguments}
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=args if isinstance(args, dict) else {"_raw": args},
                    )
                )
        return ProviderResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason,
        )

    def stream_chat(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        on_event: Callable[[Any], None] | None = None,
    ) -> ProviderResponse:
        """Stream a completion when the provider supports it.

        Emits StreamEngine events via on_event. Falls back to a single
        non-streaming call when streaming fails or is unavailable.
        """
        from hex_cli.streaming.engine import StreamEngine, StreamEvent, StreamKind

        payload_messages = [m.to_dict() for m in messages]
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": payload_messages,
            "temperature": temperature,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        engine = StreamEngine(on_event=on_event)
        try:
            stream = self._client.chat.completions.create(**kwargs)
            for chunk in stream:
                if engine.cancelled:
                    break
                engine.handle_openai_chunk(chunk)
            # Build final ProviderResponse from accumulated state
            tool_calls: list[ToolCall] = []
            for buf in engine._tool_buffers.values():
                if not buf.get("id"):
                    continue
                try:
                    args = json.loads(buf.get("arguments") or "{}")
                except json.JSONDecodeError:
                    args = {"_raw": buf.get("arguments")}
                tool_calls.append(
                    ToolCall(
                        id=buf["id"],
                        name=buf.get("name") or "unknown",
                        arguments=args if isinstance(args, dict) else {"_raw": args},
                    )
                )
            return ProviderResponse(
                content=engine.accumulated_text or None,
                tool_calls=tool_calls,
                finish_reason="stop",
            )
        except Exception:
            # Honest fallback: non-streaming request
            resp = self.chat(messages, tools=tools, temperature=temperature)
            engine.finalize_non_streaming(resp.content, resp.tool_calls)
            return resp

    def list_models(self) -> list[str]:
        """Best-effort list of models from the provider."""
        try:
            models = self._client.models.list()
            return sorted(m.id for m in models.data)
        except Exception:
            return [self.model]


class ProviderError(Exception):
    """User-facing provider error."""
    pass


def create_provider(
    config: ProviderConfig,
    model: str | None = None,
    *,
    require_key: bool = True,
) -> BaseProvider:
    return BaseProvider(config, model=model, require_key=require_key)
