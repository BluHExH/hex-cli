from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MCPClient:
    """Placeholder-capable stdio client boundary.

    Full MCP protocol is OPTIONAL for v2.0 core. This type exists so the agent
    architecture can depend on an interface without claiming production MCP parity.
    """

    command: list[str]

    def list_tools(self) -> list[str]:
        return []

    def call_tool(self, name: str, arguments: dict) -> str:
        raise NotImplementedError("MCP stdio runtime not enabled in HEX CLI 2.0.0 core")
