"""Core agent loop: plan → tool calls → execute → observe → repeat."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Callable

from hex_cli.agent.prompts import build_system_prompt
from hex_cli.agents.types import AgentKind, AgentProfile, get_agent
from hex_cli.changes.tracker import ChangeTracker
from hex_cli.config import AppConfig
from hex_cli.context import discover_project_summary, load_key_file_snippets
from hex_cli.permissions import PermissionManager
from hex_cli.providers.base import (
    BaseProvider,
    ChatMessage,
    ProviderError,
    ToolCall,
)
from hex_cli.tools.commands import CommandTools
from hex_cli.tools.filesystem import FileSystemTools
from hex_cli.tools.git_tools import GitTools
from hex_cli.tools.project import ProjectTools
from hex_cli.tools.registry import openai_tool_schemas, get_tool_spec, list_tools_for_display
from hex_cli import ui


class AgentLoop:
    def __init__(
        self,
        project_root: Path,
        provider: BaseProvider,
        config: AppConfig,
        permissions: PermissionManager,
        ui_hooks: dict[str, Callable[..., Any]] | None = None,
        agent: AgentKind | str | AgentProfile = AgentKind.GENERAL,
    ):
        self.root = project_root.resolve()
        self.provider = provider
        self.config = config
        self.permissions = permissions
        self._hooks = ui_hooks or {}

        self.fs = FileSystemTools(self.root, permissions, config)
        self.cmd = CommandTools(self.root, permissions, config)
        self.git = GitTools(self.root, permissions, config)
        self.project = ProjectTools(self.root, permissions, config)
        self.changes = ChangeTracker(self.root)

        if isinstance(agent, AgentProfile):
            self.agent_profile = agent
        else:
            self.agent_profile = get_agent(agent)

        self.messages: list[ChatMessage] = []
        self.plan_mode: bool = self.agent_profile.plan_only
        self._cancel = threading.Event()
        self._delegation_depth = 0
        self._init_system()

    def request_cancel(self) -> None:
        self._cancel.set()

    def clear_cancel(self) -> None:
        self._cancel.clear()

    def _ui(self, name: str, *args: Any, **kwargs: Any) -> Any:
        hook = self._hooks.get(name)
        if hook is not None:
            return hook(*args, **kwargs)
        fn = getattr(ui, name, None)
        if callable(fn):
            return fn(*args, **kwargs)
        return None

    def set_agent(self, kind: AgentKind | str) -> AgentProfile:
        """Switch active agent profile and refresh system prompt."""
        self.agent_profile = get_agent(kind)
        self.plan_mode = self.agent_profile.plan_only
        self._init_system()
        return self.agent_profile

    def _init_system(self) -> None:
        summary = discover_project_summary(self.root)
        snippets = load_key_file_snippets(self.root)
        base = build_system_prompt(summary, snippets)
        agent_block = (
            f"\n\n## Active agent: {self.agent_profile.display_name}\n\n"
            + self.agent_profile.system_instructions
        )
        system = base + agent_block
        self.messages = [ChatMessage(role="system", content=system)]

    def reset_context(self) -> None:
        self._init_system()
        self._ui("print_info", "Conversation context cleared.")


    def _chat_with_optional_stream(self, tools: list) -> Any:
        """Prefer streaming when provider supports it; fall back to chat()."""
        self._streamed_this_step = False
        stream_start = self._hooks.get("on_stream_start")
        stream_token = self._hooks.get("on_stream_token")
        stream_end = self._hooks.get("on_stream_end")
        if hasattr(self.provider, "stream_chat") and stream_token:
            try:
                if stream_start:
                    stream_start()
                content_parts: list[str] = []
                tool_calls = []
                for event in self.provider.stream_chat(self.messages, tools=tools):
                    if self._cancel.is_set():
                        break
                    kind = getattr(event, "kind", None)
                    # StreamEvent or duck-typed
                    name = getattr(kind, "name", str(kind) if kind is not None else "")
                    if name in ("TOKEN", "token", "text") or getattr(event, "text", None):
                        tok = getattr(event, "text", None) or getattr(event, "token", None) or ""
                        if tok:
                            content_parts.append(tok)
                            stream_token(tok)
                            self._streamed_this_step = True
                    elif name in ("TOOL_CALL", "tool_call"):
                        tool_calls.append(event)
                    elif name in ("DONE", "done", "error"):
                        break
                if stream_end:
                    stream_end()
                from hex_cli.providers.base import ChatResponse, ToolCall
                content = "".join(content_parts)
                # If stream yielded nothing useful, fall back
                if not content and not tool_calls:
                    return self.provider.chat(self.messages, tools=tools)
                # Rebuild tool calls if present on events
                tcs = []
                for ev in tool_calls:
                    if hasattr(ev, "tool_call"):
                        tcs.append(ev.tool_call)
                return ChatResponse(content=content, tool_calls=tcs or None)
            except Exception:
                # Fall back to non-streaming
                if stream_end:
                    try:
                        stream_end()
                    except Exception:
                        pass
                return self.provider.chat(self.messages, tools=tools)
        return self.provider.chat(self.messages, tools=tools)


    def run(self, user_task: str, *, plan_only: bool | None = None) -> str:
        """Process a single user task through the agent loop."""
        self.clear_cancel()
        effective_plan = self.agent_profile.plan_only if plan_only is None else plan_only
        self.plan_mode = effective_plan
        task = user_task
        if effective_plan:
            task = (
                "[PLAN MODE — do not call write_file, edit_file, apply_patch, "
                "create_directory, or run_command. Only analyze and propose a plan.]\n\n"
                + user_task
            )
        self.messages.append(ChatMessage(role="user", content=task))

        final_text = ""
        steps = 0
        max_steps = self.config.max_agent_steps
        tools = openai_tool_schemas(self.agent_profile.allowed_tools)

        while steps < max_steps:
            if self._cancel.is_set():
                self._ui("print_warning", "Agent cancelled.")
                break
            steps += 1
            spinner_ctx = self._ui("spinner", f"Thinking (step {steps}/{max_steps})…")
            try:
                response = self._chat_with_optional_stream(tools)
            except ProviderError as e:
                self._ui("print_error", str(e))
                return str(e)
            except Exception as e:
                self._ui("print_error", f"Unexpected error: {e}")
                return str(e)
            finally:
                # spinner contexts from Rich are optional no-ops in TUI
                pass

            assistant_msg = ChatMessage(role="assistant", content=response.content)
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

            # Avoid double-printing when tokens already streamed to UI
            if response.content and not getattr(self, "_streamed_this_step", False):
                self._ui("print_assistant", response.content)
            final_text = response.content or final_text

            if not response.tool_calls:
                break

            for tc in response.tool_calls:
                if self._cancel.is_set():
                    self._ui("print_warning", "Agent cancelled during tool execution.")
                    break
                # Enforce agent tool allow-list + plan mode
                if tc.name not in self.agent_profile.allowed_tools:
                    result = {
                        "ok": False,
                        "skipped": True,
                        "error": f"Tool '{tc.name}' not permitted for {self.agent_profile.display_name} agent",
                    }
                    self._ui("print_tool_status", tc.name, "skipped", "agent policy")
                elif effective_plan and tc.name in {
                    "write_file", "edit_file", "apply_patch",
                    "create_directory", "run_command", "run_tests",
                    "git_stage", "git_commit", "git_checkout",
                }:
                    result = {
                        "ok": False,
                        "skipped": True,
                        "error": "Blocked in plan mode — no file/command mutations",
                    }
                    self._ui("print_tool_status", tc.name, "skipped", "plan mode")
                else:
                    result = self._dispatch_tool(tc)
                    self._track_change(tc.name, result)

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
            self._ui(
                "print_warning",
                f"Reached maximum agent steps ({max_steps}). "
                "Increase max_agent_steps in config if needed.",
            )

        # Change summary
        summary = self.changes.summary()
        if summary["file_count"]:
            lines = [f"Changes: {summary['file_count']} file(s)  +{summary['added']}  -{summary['removed']}"]
            for f in summary["files"]:
                lines.append(f"  • {f['path']} ({f['action']}) +{f['added']}/-{f['removed']}")
            self._ui("print_info", "\n".join(lines))

        return final_text

    def _track_change(self, tool_name: str, result: dict[str, Any]) -> None:
        if not result.get("ok"):
            return
        path = result.get("path")
        if not path:
            return
        if tool_name == "write_file":
            before = result.get("before")  # may be None for create
            after = result.get("content") or result.get("after")
            # write_file may not return content — re-read if needed
            if after is None and path:
                try:
                    after = (self.root / str(path)).read_text(encoding="utf-8", errors="replace")
                except OSError:
                    after = None
            action = "create" if before is None and result.get("created") else "modify"
            if "created" in result or result.get("action") == "create":
                action = "create"
            self.changes.record(str(path), action, before, after)
        elif tool_name in ("edit_file", "apply_patch"):
            self.changes.record(
                str(path),
                "modify",
                result.get("before"),
                result.get("after"),
            )

    def _dispatch_tool(self, tc: ToolCall) -> dict[str, Any]:
        name = tc.name
        args = tc.arguments if isinstance(tc.arguments, dict) else {}

        if "_raw" in args and len(args) == 1:
            self._ui("print_tool_status", name, "error", "invalid JSON arguments")
            return {"ok": False, "error": "Tool arguments were not valid JSON"}

        self._ui("print_tool_status", name, "running", self._short_args(name, args))

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
            "glob": lambda: self.fs.glob(
                pattern=str(args.get("pattern", "")),
                path=args.get("path", "."),
                max_results=int(args.get("max_results", 100)),
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
            "apply_patch": lambda: self.fs.apply_patch(
                path=str(args.get("path", "")),
                patch=str(args.get("patch", "")),
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
            "git_branches": lambda: self.git.git_branches(),
            "git_log": lambda: self.git.git_log(
                max_count=int(args.get("max_count", 15)),
            ),
            "git_stage": lambda: self.git.git_stage(
                paths=args.get("paths"),
            ),
            "git_commit": lambda: self.git.git_commit(
                message=str(args.get("message", "")),
            ),
            "git_checkout": lambda: self.git.git_checkout(
                branch=str(args.get("branch", "")),
                create=bool(args.get("create", False)),
            ),
            "project_overview": lambda: self.project.project_overview(),
            "detect_project_type": lambda: self.project.detect_project_type(),
        }

        handler = handlers.get(name)
        if handler is None:
            self._ui("print_tool_status", name, "error", "unknown tool")
            return {"ok": False, "error": f"Unknown tool: {name}"}

        if name in ("read_file", "write_file", "edit_file", "create_directory", "apply_patch"):
            if not args.get("path"):
                self._ui("print_tool_status", name, "error", "missing path")
                return {"ok": False, "error": "path is required"}
        if name in ("search_text", "glob") and not args.get("pattern"):
            self._ui("print_tool_status", name, "error", "missing pattern")
            return {"ok": False, "error": "pattern is required"}
        if name == "run_command" and not args.get("command"):
            self._ui("print_tool_status", name, "error", "missing command")
            return {"ok": False, "error": "command is required"}
        if name == "write_file" and "content" not in args:
            self._ui("print_tool_status", name, "error", "missing content")
            return {"ok": False, "error": "content is required"}
        if name == "edit_file" and ("old_string" not in args or "new_string" not in args):
            self._ui("print_tool_status", name, "error", "missing old_string/new_string")
            return {"ok": False, "error": "old_string and new_string are required"}
        if name == "apply_patch" and "patch" not in args:
            self._ui("print_tool_status", name, "error", "missing patch")
            return {"ok": False, "error": "patch is required"}

        try:
            result = handler()
        except Exception as e:
            self._ui("print_tool_status", name, "error", str(e)[:80])
            return {"ok": False, "error": str(e)}

        if result.get("skipped"):
            self._ui(
                "print_tool_status",
                name,
                "skipped",
                result.get("error", "rejected"),
                "",
                str(result.get("error", "rejected")),
            )
        elif result.get("ok"):
            detail = ""
            if "path" in result:
                detail = str(result["path"])
            elif "count" in result:
                detail = f"{result['count']} hits"
            elif "matches" in result:
                detail = f"{len(result['matches'])} files"
            elif "command" in result:
                detail = str(result.get("command", ""))[:80]
            # Build safe output preview (no secrets)
            preview_parts = []
            for k in ("stdout", "output", "content", "diff", "message", "summary"):
                if result.get(k):
                    preview_parts.append(str(result[k])[:2000])
            if "files" in result and isinstance(result["files"], list):
                preview_parts.append("\n".join(str(x) for x in result["files"][:40]))
            if "matches" in result and isinstance(result["matches"], list):
                preview_parts.append("\n".join(str(x) for x in result["matches"][:40]))
            output = "\n".join(preview_parts)[:4000]
            self._ui("print_tool_status", name, "ok", detail, output, "")
        else:
            self._ui(
                "print_tool_status",
                name,
                "error",
                str(result.get("error", ""))[:80],
                "",
                str(result.get("error", ""))[:500],
            )

        return result

    def _short_args(self, name: str, args: dict[str, Any]) -> str:
        if "path" in args:
            return str(args["path"])
        if "command" in args:
            c = str(args["command"])
            return c if len(c) < 60 else c[:57] + "…"
        if "pattern" in args:
            return str(args["pattern"])
        return ""

    def tools_list(self) -> list[dict[str, str]]:
        return list_tools_for_display()
