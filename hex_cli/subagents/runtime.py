"""True parallel subagent execution with isolation and limits.

Each subagent gets an independent message context and tool policy.
Results are structured and merged by the parent. Cancellation propagates.
"""

from __future__ import annotations

import concurrent.futures
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from hex_cli.agents.types import AgentKind, AgentProfile, get_agent
from hex_cli.config import AppConfig
from hex_cli.permissions import PermissionManager


@dataclass
class DelegationLimits:
    max_depth: int = 2
    max_concurrent: int = 3
    max_steps_per_child: int = 12
    timeout_seconds: float = 180.0


@dataclass
class SubagentResult:
    task_id: str
    agent: str
    ok: bool
    summary: str
    output: str = ""
    error: str | None = None
    changes: list[dict[str, Any]] = field(default_factory=list)
    duration_ms: int = 0
    cancelled: bool = False


@dataclass
class SubagentTask:
    task_id: str
    prompt: str
    agent: AgentKind
    parent_depth: int = 0


class SubagentRuntime:
    """Manages concurrent child agent runs under a parent."""

    def __init__(
        self,
        project_root: Path,
        config: AppConfig,
        permissions: PermissionManager,
        provider_factory: Callable[[], Any],
        limits: DelegationLimits | None = None,
        ui_hooks: dict[str, Callable[..., Any]] | None = None,
    ):
        self.root = project_root.resolve()
        self.config = config
        self.permissions = permissions
        self._provider_factory = provider_factory
        self.limits = limits or DelegationLimits()
        self._hooks = ui_hooks or {}
        self._cancel = threading.Event()
        self._active = 0
        self._lock = threading.Lock()

    def request_cancel(self) -> None:
        self._cancel.set()

    def clear_cancel(self) -> None:
        self._cancel.clear()

    def can_delegate(self, profile: AgentProfile, depth: int) -> bool:
        if not profile.can_delegate:
            return False
        if depth >= min(profile.max_delegation_depth, self.limits.max_depth):
            return False
        return True

    def run_one(
        self,
        prompt: str,
        agent: AgentKind | str = AgentKind.EXPLORE,
        *,
        depth: int = 0,
        plan_only: bool | None = None,
    ) -> SubagentResult:
        """Run a single isolated subagent (blocking)."""
        task_id = uuid.uuid4().hex[:10]
        profile = get_agent(agent)
        if depth > self.limits.max_depth:
            return SubagentResult(
                task_id=task_id,
                agent=profile.id,
                ok=False,
                summary="Delegation depth exceeded",
                error=f"depth {depth} > max {self.limits.max_depth}",
            )

        start = time.time()
        try:
            from hex_cli.agent.loop import AgentLoop

            provider = self._provider_factory()
            loop = AgentLoop(
                self.root,
                provider,
                self.config,
                self.permissions,
                ui_hooks=self._hooks,
                agent=profile,
            )
            # Cap child steps
            original_max = self.config.max_agent_steps
            try:
                self.config.max_agent_steps = min(original_max, self.limits.max_steps_per_child)
                if self._cancel.is_set():
                    return SubagentResult(
                        task_id=task_id,
                        agent=profile.id,
                        ok=False,
                        summary="Cancelled before start",
                        cancelled=True,
                    )
                text = loop.run(prompt, plan_only=plan_only)
                changes = [
                    {"path": r.path, "action": r.action}
                    for r in loop.changes.records
                ]
                return SubagentResult(
                    task_id=task_id,
                    agent=profile.id,
                    ok=True,
                    summary=(text or "")[:500],
                    output=text or "",
                    changes=changes,
                    duration_ms=int((time.time() - start) * 1000),
                    cancelled=self._cancel.is_set(),
                )
            finally:
                self.config.max_agent_steps = original_max
        except Exception as e:
            return SubagentResult(
                task_id=task_id,
                agent=profile.id,
                ok=False,
                summary="Subagent failed",
                error=str(e),
                duration_ms=int((time.time() - start) * 1000),
            )

    def run_parallel(
        self,
        tasks: list[tuple[str, AgentKind | str]],
        *,
        depth: int = 0,
    ) -> list[SubagentResult]:
        """Run multiple subagents concurrently with a concurrency limit."""
        if not tasks:
            return []
        max_workers = max(1, min(self.limits.max_concurrent, len(tasks)))
        results: list[SubagentResult] = []

        def _worker(item: tuple[str, AgentKind | str]) -> SubagentResult:
            prompt, agent = item
            with self._lock:
                self._active += 1
            try:
                return self.run_one(prompt, agent, depth=depth)
            finally:
                with self._lock:
                    self._active -= 1

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(_worker, t) for t in tasks]
            for fut in concurrent.futures.as_completed(futures):
                if self._cancel.is_set():
                    for f in futures:
                        f.cancel()
                try:
                    results.append(fut.result(timeout=self.limits.timeout_seconds))
                except Exception as e:
                    results.append(
                        SubagentResult(
                            task_id=uuid.uuid4().hex[:8],
                            agent="unknown",
                            ok=False,
                            summary="Future failed",
                            error=str(e),
                        )
                    )
        return results

    def merge_results(self, results: list[SubagentResult]) -> str:
        """Produce a parent-facing summary from child results."""
        lines = [f"Subagent results ({len(results)}):"]
        for r in results:
            status = "ok" if r.ok else ("cancelled" if r.cancelled else "error")
            lines.append(f"- [{r.agent}/{r.task_id}] {status} ({r.duration_ms}ms)")
            if r.summary:
                lines.append(f"  {r.summary[:200]}")
            if r.error:
                lines.append(f"  error: {r.error}")
            if r.changes:
                lines.append(f"  changes: {len(r.changes)} file(s)")
        return "\n".join(lines)
