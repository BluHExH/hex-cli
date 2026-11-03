from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hex_cli import __version__
from hex_cli.logging_ext import setup_logging


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hex", description="HEX CLI — AI coding agent")
    parser.add_argument("--version", action="version", version=f"HEX CLI {__version__}")
    parser.add_argument("--workspace", type=str, default=".", help="Project workspace root")
    parser.add_argument("--log-level", type=str, default="WARNING")
    parser.add_argument(
        "--permission",
        choices=["allow", "deny", "prompt"],
        default=None,
        help="Override permission mode for headless runs",
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="Optional one-shot prompt (headless mock/agent turn)",
    )
    args = parser.parse_args(argv)
    setup_logging(args.log_level)
    workspace = Path(args.workspace).resolve()

    if args.prompt:
        from hex_cli.agent.runner import AgentRunner
        from hex_cli.changes.tracker import ChangeLog
        from hex_cli.config.settings import load_settings
        from hex_cli.permissions.gate import PermissionGate
        from hex_cli.providers.factory import create_provider
        from hex_cli.tools.registry import ToolRegistry

        settings = load_settings(workspace)
        settings.workspace = str(workspace)
        mode = args.permission or settings.permission_mode or "allow"
        settings.permission_mode = mode
        gate = PermissionGate(mode=mode)
        tools = ToolRegistry(workspace, gate)
        provider = create_provider(settings)
        runner = AgentRunner(provider, tools, settings, ChangeLog())
        result = runner.run_turn([], args.prompt)
        print(result.assistant_text)
        return 0

    try:
        from hex_cli.tui.app import HexApp
    except ImportError as exc:
        print(f"TUI dependencies missing: {exc}", file=sys.stderr)
        return 1
    app = HexApp(workspace=workspace)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
