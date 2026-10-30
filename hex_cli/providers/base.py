"""OpenAI-compatible provider abstraction.

Supports OpenAI, Ollama, OpenRouter, Groq, and any endpoint that
speaks the OpenAI chat-completions + tools API.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError

from hex_cli.config import ProviderConfig, get_api_key


@dataclass
class ChatMessage:
    role: str
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


TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories under a relative path inside the project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path (default '.')", "default": "."},
                    "recursive": {"type": "boolean", "description": "Recurse into subdirectories", "default": False},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a text file inside the project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path"},
                    "offset": {"type": "integer", "description": "1-based start line (optional)"},
                    "limit": {"type": "integer", "description": "Max lines to return (optional)"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_text",
            "description": "Search for a text pattern across project source files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Text or regex pattern"},
                    "path": {"type": "string", "description": "Relative directory to search (default '.')", "default": "."},
                    "max_results": {"type": "integer", "description": "Maximum matches to return", "default": 30},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create a new file or overwrite an existing one. Requires user approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path"},
                    "content": {"type": "string", "description": "Full file content"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Apply a search-and-replace edit to an existing file. Requires user approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path"},
                    "old_string": {"type": "string", "description": "Exact text to find"},
                    "new_string": {"type": "string", "description": "Replacement text"},
                    "replace_all": {"type": "boolean", "description": "Replace every occurrence", "default": False},
                },
                "required": ["path", "old_string", "new_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_directory",
            "description": "Create a directory (and parents) inside the project. Requires approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative directory path"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command inside the project directory. Requires user approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                    "timeout": {"type": "number", "description": "Timeout in seconds (optional)"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_status",
            "description": "Show git status for the current repository.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_diff",
            "description": "Show git diff (unstaged by default, or staged).",
            "parameters": {
                "type": "object",
                "properties": {
                    "staged": {"type": "boolean", "description": "Show staged diff", "default": False},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": "Run the project's test suite (pytest by default).",
            "parameters": {
                "type": "object",
                "properties": {
                    "args": {"type": "string", "description": "Extra arguments for the test runner", "default": ""},
                },
            },
        },
    },
]


class BaseProvider:
    """Thin wrapper around the OpenAI-compatible Chat Completions API."""

    def __init__(self, config: ProviderConfig, model: str | None = None):
        self.config = config
        self.model = model or config.default_model
        api_key = get_api_key(config)
        if not api_key and config.name != "ollama":
            raise ValueError(
                f"API key not found. Set the environment variable {config.api_key_env} "
                f"or add it to a .env file. See `hex doctor` for diagnostics."
            )
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
                time.sleep(2 ** attempt)
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

    def list_models(self) -> list[str]:
        try:
            models = self._client.models.list()
            return sorted(m.id for m in models.data)
        except Exception:
            return [self.model]


class ProviderError(Exception):
    """User-facing provider error."""
    pass


def create_provider(config: ProviderConfig, model: str | None = None) -> BaseProvider:
    return BaseProvider(config, model=model)
