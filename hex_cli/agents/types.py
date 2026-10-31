"""Specialized agent profiles: build, plan, explore, general."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet


class AgentKind(str, Enum):
    BUILD = "build"
    PLAN = "plan"
    EXPLORE = "explore"
    GENERAL = "general"


# Tools each agent is allowed to request
_READ_TOOLS = frozenset({
    "list_files", "read_file", "search_text", "glob",
    "project_overview", "detect_project_type",
    "git_status", "git_diff",
})
_WRITE_TOOLS = frozenset({
    "write_file", "edit_file", "apply_patch", "create_directory",
})
_EXEC_TOOLS = frozenset({
    "run_command", "run_tests",
})
_GIT_WRITE = frozenset({
    "git_stage", "git_commit", "git_checkout",
})


@dataclass(frozen=True)
class AgentProfile:
    kind: AgentKind
    display_name: str
    description: str
    system_instructions: str
    allowed_tools: FrozenSet[str]
    plan_only: bool = False
    can_delegate: bool = False
    max_delegation_depth: int = 0

    @property
    def id(self) -> str:
        return self.kind.value


BUILD_INSTRUCTIONS = """You are the HEX Build Agent — a senior software engineer focused on implementing real changes.

Your responsibilities:
- Implement features, fix bugs, and write tests using the available tools.
- Inspect the codebase before editing.
- Prefer precise edits (edit_file / apply_patch) over full rewrites.
- Track every modification; the ChangeTracker will record them.
- After meaningful changes, run or propose tests.
- Summarize completed work clearly when finished.

Rules:
- Respect permission prompts. If a tool is denied, adapt or ask the user.
- Stay inside the project root. Never traverse outside.
- Never print secrets or commit credentials.
- Work efficiently; avoid unnecessary tool calls.
"""

PLAN_INSTRUCTIONS = """You are the HEX Plan Agent — an architect that produces actionable implementation plans.

Your responsibilities:
- Analyze the user request and the relevant codebase.
- Explore files with read-only tools only.
- Produce a clear, ordered implementation plan with concrete steps.
- Identify risks, dependencies, and test strategy.
- Do NOT modify any files or run mutating commands.

Rules:
- You operate in plan-only mode. Write tools and shell commands are unavailable.
- Be specific: name files, functions, and expected outcomes.
- Prefer short, high-signal plans over long essays.
"""

EXPLORE_INSTRUCTIONS = """You are the HEX Explore Agent — a codebase investigator and explainer.

Your responsibilities:
- Search and read the project to answer architecture and design questions.
- Explain modules, data flows, and conventions.
- Point to specific files and line ranges when helpful.
- Do NOT modify project files.

Rules:
- Read-only tools only. No writes, no shell that mutates state.
- Prefer accurate references over speculation.
"""

GENERAL_INSTRUCTIONS = """You are HEX, a helpful AI coding assistant.

You can answer development questions, explain concepts, and when appropriate use tools to inspect the project.
For substantial code changes, prefer switching to the Build agent (/build) or Plan agent (/plan).

Rules:
- Permission-first for any mutating action.
- Stay inside the project root.
- Never expose secrets.
"""


_PROFILES: dict[AgentKind, AgentProfile] = {
    AgentKind.BUILD: AgentProfile(
        kind=AgentKind.BUILD,
        display_name="Build",
        description="Implements code changes with full tool access.",
        system_instructions=BUILD_INSTRUCTIONS,
        allowed_tools=_READ_TOOLS | _WRITE_TOOLS | _EXEC_TOOLS | _GIT_WRITE,
        plan_only=False,
        can_delegate=True,
        max_delegation_depth=2,
    ),
    AgentKind.PLAN: AgentProfile(
        kind=AgentKind.PLAN,
        display_name="Plan",
        description="Analyzes and produces implementation plans (read-only).",
        system_instructions=PLAN_INSTRUCTIONS,
        allowed_tools=_READ_TOOLS,
        plan_only=True,
        can_delegate=False,
        max_delegation_depth=0,
    ),
    AgentKind.EXPLORE: AgentProfile(
        kind=AgentKind.EXPLORE,
        display_name="Explore",
        description="Investigates and explains the codebase (read-only).",
        system_instructions=EXPLORE_INSTRUCTIONS,
        allowed_tools=_READ_TOOLS,
        plan_only=False,
        can_delegate=False,
        max_delegation_depth=0,
    ),
    AgentKind.GENERAL: AgentProfile(
        kind=AgentKind.GENERAL,
        display_name="General",
        description="General development assistance and Q&A.",
        system_instructions=GENERAL_INSTRUCTIONS,
        allowed_tools=_READ_TOOLS | _WRITE_TOOLS | _EXEC_TOOLS,
        plan_only=False,
        can_delegate=True,
        max_delegation_depth=1,
    ),
}


def get_agent(kind: AgentKind | str) -> AgentProfile:
    if isinstance(kind, str):
        kind = AgentKind(kind.lower())
    return _PROFILES[kind]


def list_agents() -> list[AgentProfile]:
    return list(_PROFILES.values())
