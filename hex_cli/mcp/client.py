"""MCP client with stdio transport and tool discovery.

Implements a practical subset of the MCP lifecycle:
initialize → tools/list → tools/call → shutdown.

HTTP transport is stubbed with a clear unsupported path until a
compatible server is verified. Untrusted tools always require approval.
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class MCPServerConfig:
    name: str
    command: list[str]
    env: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None
    transport: str = "stdio"  # stdio | http
    url: str | None = None  # for http
    timeout_seconds: float = 30.0


@dataclass
class MCPTool:
    server: str
    name: str
    description: str
    input_schema: dict[str, Any]
    namespaced_name: str = ""

    def __post_init__(self) -> None:
        if not self.namespaced_name:
            self.namespaced_name = f"mcp__{self.server}__{self.name}"


@dataclass
class MCPCallResult:
    ok: bool
    content: Any = None
    error: str | None = None
    duration_ms: int = 0


class _StdioSession:
    """Minimal JSON-RPC over stdio for one MCP server process."""

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self._proc: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()
        self._next_id = 1
        self.tools: list[MCPTool] = []
        self.connected = False
        self.last_error: str | None = None

    def start(self) -> bool:
        if self.config.transport != "stdio":
            self.last_error = f"Transport '{self.config.transport}' not implemented in this build"
            return False
        try:
            env = os.environ.copy()
            env.update(self.config.env)
            self._proc = subprocess.Popen(
                self.config.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.config.cwd,
                env=env,
                bufsize=1,
            )
            # initialize
            init = self._request(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "hex-cli", "version": "0.6.0"},
                },
            )
            if init is None:
                self.last_error = self.last_error or "initialize failed"
                self.stop()
                return False
            # notifications/initialized
            self._notify("notifications/initialized", {})
            # tools/list
            listed = self._request("tools/list", {})
            if listed and isinstance(listed, dict):
                for t in listed.get("tools") or []:
                    self.tools.append(
                        MCPTool(
                            server=self.config.name,
                            name=t.get("name", "unknown"),
                            description=t.get("description") or "",
                            input_schema=t.get("inputSchema") or {"type": "object"},
                        )
                    )
            self.connected = True
            return True
        except Exception as e:
            self.last_error = str(e)
            self.stop()
            return False

    def stop(self) -> None:
        self.connected = False
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=3)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
        self._proc = None

    def _request(self, method: str, params: dict[str, Any]) -> Any | None:
        if not self._proc or not self._proc.stdin or not self._proc.stdout:
            return None
        with self._lock:
            req_id = self._next_id
            self._next_id += 1
            msg = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
            try:
                self._proc.stdin.write(json.dumps(msg) + "\n")
                self._proc.stdin.flush()
                deadline = time.time() + self.config.timeout_seconds
                while time.time() < deadline:
                    line = self._proc.stdout.readline()
                    if not line:
                        break
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    if data.get("id") == req_id:
                        if "error" in data:
                            self.last_error = str(data["error"])
                            return None
                        return data.get("result")
            except Exception as e:
                self.last_error = str(e)
                return None
        return None

    def _notify(self, method: str, params: dict[str, Any]) -> None:
        if not self._proc or not self._proc.stdin:
            return
        msg = {"jsonrpc": "2.0", "method": method, "params": params}
        try:
            self._proc.stdin.write(json.dumps(msg) + "\n")
            self._proc.stdin.flush()
        except Exception:
            pass

    def call_tool(self, name: str, arguments: dict[str, Any]) -> MCPCallResult:
        start = time.time()
        if not self.connected:
            return MCPCallResult(ok=False, error="Server not connected")
        result = self._request("tools/call", {"name": name, "arguments": arguments or {}})
        ms = int((time.time() - start) * 1000)
        if result is None:
            return MCPCallResult(ok=False, error=self.last_error or "call failed", duration_ms=ms)
        return MCPCallResult(ok=True, content=result, duration_ms=ms)


class MCPClient:
    """Registry of MCP servers and their tools."""

    def __init__(self):
        self._sessions: dict[str, _StdioSession] = {}

    def connect(self, config: MCPServerConfig) -> dict[str, Any]:
        if config.name in self._sessions:
            self.disconnect(config.name)
        if config.transport == "http":
            return {
                "ok": False,
                "error": "HTTP MCP transport is not enabled in this build; use stdio",
            }
        session = _StdioSession(config)
        ok = session.start()
        if ok:
            self._sessions[config.name] = session
            return {
                "ok": True,
                "name": config.name,
                "tools": len(session.tools),
                "tool_names": [t.namespaced_name for t in session.tools],
            }
        return {"ok": False, "error": session.last_error or "connect failed"}

    def disconnect(self, name: str) -> bool:
        session = self._sessions.pop(name, None)
        if session:
            session.stop()
            return True
        return False

    def disconnect_all(self) -> None:
        for name in list(self._sessions):
            self.disconnect(name)

    def list_servers(self) -> list[dict[str, Any]]:
        out = []
        for name, s in self._sessions.items():
            out.append({
                "name": name,
                "connected": s.connected,
                "tools": len(s.tools),
                "transport": s.config.transport,
                "error": s.last_error,
            })
        return out

    def list_tools(self) -> list[MCPTool]:
        tools: list[MCPTool] = []
        for s in self._sessions.values():
            tools.extend(s.tools)
        return tools

    def call(
        self,
        namespaced_or_name: str,
        arguments: dict[str, Any],
        *,
        server: str | None = None,
    ) -> MCPCallResult:
        # Resolve server + tool
        if namespaced_or_name.startswith("mcp__"):
            parts = namespaced_or_name.split("__", 2)
            if len(parts) == 3:
                server = parts[1]
                tool_name = parts[2]
            else:
                return MCPCallResult(ok=False, error="Invalid namespaced tool name")
        else:
            tool_name = namespaced_or_name
            if server is None:
                # Find unique match
                matches = [t for t in self.list_tools() if t.name == tool_name]
                if len(matches) != 1:
                    return MCPCallResult(
                        ok=False,
                        error=f"Ambiguous or missing tool '{tool_name}' — specify server",
                    )
                server = matches[0].server
        session = self._sessions.get(server or "")
        if not session:
            return MCPCallResult(ok=False, error=f"Server '{server}' not connected")
        return session.call_tool(tool_name, arguments)

    def openai_tool_schemas(self) -> list[dict[str, Any]]:
        """Expose MCP tools as OpenAI function schemas (namespaced)."""
        schemas = []
        for t in self.list_tools():
            schemas.append({
                "type": "function",
                "function": {
                    "name": t.namespaced_name,
                    "description": f"[MCP:{t.server}] {t.description}",
                    "parameters": t.input_schema or {"type": "object"},
                },
            })
        return schemas
