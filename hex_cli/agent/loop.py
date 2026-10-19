"""Core agent loop: plan → tool calls → execute → observe → repeat."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from hex_cli.agent.prompts import build_system_prompt
from hex_cli.config import AppConfig
from hex_cli.context import discover_project_summary, load_key_file_snippets
from hex_cli.permissions import PermissionManager
from hex_cli.providers.base import (
    TOOL_SCHEMAS,
    BaseProvider,
    ChatMessage,
    ProviderError,
    ToolCall,
)
from hex_cli.tools.commands import CommandTools
from hex_cli.tools.filesystem import FileSystemTools
from hex_cli.tools.git_tools import GitTools
from hex_cli import ui


class AgentLoop:
    def __init__(
        self,
        project_root: Path,
        provider: BaseProvider,
        config: AppConfig,
        permissions: PermissionManager,
    ):
        self.root = project_root.resolve()
        self.provider = provider
        self.config = config
        self.permissions = permissions

        self.fs = FileSystemTools(self.root, permissions, config)
        self.cmd = CommandTools(self.root, permissions, config)
        self.git = GitTools(self.root, permissions, config)

        self.messages: list[ChatMessage] = []
        self._init_system()

    def _init_system(self) -> None:
        summary = discover_project_summary(self.root)
        snippets = load_key_file_snippets(self.root)
        system = build_system_prompt(summary, snippets)
        self.messages = [ChatMessage(role="system", content=system)]

    def reset_context(self) -> None:
        self._init_system()
        ui.print_info("Conversation context cleared.")

    def run(self, user_task: str) -> str:
        """Process a single user task through the agent loop."""
        self.messages.append(ChatMessage(role="user", content=user_task))

        final_text = ""
        steps = 0
        max_steps = self.config.max_agent_steps

        while steps < max_steps:
            steps += 1
            with ui.spinner(f"Thinking (step {steps}/{max_steps})…") as progress:
                progress.add_task("think")
                try:
                    response = self.provider.chat(self.messages, tools=TOOL_SCHEMAS)
                except ProviderError as e:
                    ui.print_error(str(e))
                    return str(e)
                except Exception as e:
                    ui.print_error(f"Unexpected error: {e}")
                    return str(e)

            # Record assistant message
            assistant_msg = ChatMessage(
                role="assistant",
                content=response.content,
            )
            if response.tool_calls:
                assistant_msg.tool_calls = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in response.tool_calls
                ]
            self.messages.append(assistant_msg)

            if response.content:
                ui.print_assistant(response.content)
                final_text = response.content

            if not response.tool_calls:
                # Model is done
                break

            # Execute tools
            for tc in response.tool_calls:
                result = self._dispatch_tool(tc)
                result_str = json.dumps(result, ensure_ascii=False, default=str)
                if len(result_str) > 20_000:
                    result_str = result_str[:20_000] + "…(truncated)"

                self.messages.append(
                    ChatMessage(
                        role="tool",
                        tool_call_id=tc.id,
                        name=tc.name,
                        content=result_str,
                    )
                )

        if steps >= max_steps:
            ui.print_warning(
                f"Reached maximum agent steps ({max_steps}). "
                "Increase max_agent_steps in config if needed."
            )

        return final_text

    def _dispatch_tool(self, tc: ToolCall) -> dict[str, Any]:
        name = tc.name
        args = tc.arguments if isinstance(tc.arguments, dict) else {}

        # Reject raw/invalid argument blobs
        if "_raw" in args and len(args) == 1:
            ui.print_tool_status(name, "error", "invalid JSON arguments")
            return {"ok": False, "error": "Tool arguments were not valid JSON"}

        ui.print_tool_status(name, "running", self._short_args(name, args))

        handlers: dict[str, Callable[..., dict[str, Any]]] = {
            "list_files": lambda: self.fs.list_files(
                path=args.get("path", "."),
                recursive=bool(args.get("recursive", False)),
            ),
            "read_file": lambda: self.fs.read_file(
                path=str(args.get("path", "")),
                offset=args.get("offset"),
                limit=args.get("limit"),
            ),
            "search_text": lambda: self.fs.search_text(
                pattern=str(args.get("pattern", "")),
                path=args.get("path", "."),
                max_results=int(args.get("max_results", 30)),
            ),
            "write_file": lambda: self.fs.write_file(
                path=str(args.get("path", "")),
                content=str(args.get("content", "")),
            ),
            "edit_file": lambda: self.fs.edit_file(
                path=str(args.get("path", "")),
                old_string=str(args.get("old_string", "")),
                new_string=str(args.get("new_string", "")),
                replace_all=bool(args.get("replace_all", False)),
            ),
            "create_directory": lambda: self.fs.create_directory(
                path=str(args.get("path", "")),
            ),
            "run_command": lambda: self.cmd.run_command(
                command=str(args.get("command", "")),
                timeout=args.get("timeout"),
            ),
            "run_tests": lambda: self.cmd.run_tests(
                args=str(args.get("args", "")),
            ),
            "git_status": lambda: self.git.git_status(),
            "git_diff": lambda: self.git.git_diff(
                staged=bool(args.get("staged", False)),
            ),
        }

        handler = handlers.get(name)
        if handler is None:
            ui.print_tool_status(name, "error", "unknown tool")
            return {"ok": False, "error": f"Unknown tool: {name}"}

        # Basic argument validation
        if name in ("read_file", "write_file", "edit_file", "create_directory"):
            if not args.get("path"):
                ui.print_tool_status(name, "error", "missing path")
                return {"ok": False, "error": "path is required"}
        if name == "search_text" and not args.get("pattern"):
            ui.print_tool_status(name, "error", "missing pattern")
            return {"ok": False, "error": "pattern is required"}
        if name == "run_command" and not args.get("command"):
            ui.print_tool_status(name, "error", "missing command")
            return {"ok": False, "error": "command is required"}
        if name == "write_file" and "content" not in args:
            ui.print_tool_status(name, "error", "missing content")
            return {"ok": False, "error": "content is required"}
        if name == "edit_file" and (
            "old_string" not in args or "new_string" not in args
        ):
            ui.print_tool_status(name, "error", "missing old_string/new_string")
            return {"ok": False, "error": "old_string and new_string are required"}

        try:
            result = handler()
        except Exception as e:
            ui.print_tool_status(name, "error", str(e)[:80])
            return {"ok": False, "error": str(e)}

        if result.get("skipped"):
            ui.print_tool_status(name, "skipped", result.get("error", "rejected"))
        elif result.get("ok"):
            detail = ""
            if "path" in result:
                detail = str(result["path"])
            elif "exit_code" in result:
                detail = f"exit {result['exit_code']}"
            elif "count" in result:
                detail = f"{result['count']} items"
            ui.print_tool_status(name, "ok", detail)
        else:
            ui.print_tool_status(name, "error", str(result.get("error", ""))[:80])

        return result

    @staticmethod
    def _short_args(name: str, args: dict[str, Any]) -> str:
        if name in ("read_file", "write_file", "edit_file", "create_directory", "list_files"):
            return str(args.get("path", ""))[:60]
        if name == "search_text":
            return str(args.get("pattern", ""))[:40]
        if name == "run_command":
            return str(args.get("command", ""))[:60]
        return ""
