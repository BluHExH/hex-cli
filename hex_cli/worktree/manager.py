"""Safe git worktree create / list / switch / remove with confirmations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hex_cli.permissions import ActionType, PermissionManager

try:
    from git import Repo, InvalidGitRepositoryError
    HAS_GIT = True
except ImportError:
    HAS_GIT = False
    Repo = None  # type: ignore


class WorktreeManager:
    def __init__(self, project_root: Path, permissions: PermissionManager | None = None):
        self.root = project_root.resolve()
        self.perms = permissions
        self._repo = None

    def _repo_obj(self):
        if not HAS_GIT:
            raise RuntimeError("GitPython not installed")
        if self._repo is None:
            try:
                self._repo = Repo(self.root, search_parent_directories=True)
            except InvalidGitRepositoryError:
                raise RuntimeError("Not a git repository")
        return self._repo

    def list_worktrees(self) -> dict[str, Any]:
        try:
            repo = self._repo_obj()
        except RuntimeError as e:
            return {"ok": False, "error": str(e)}
        try:
            raw = repo.git.worktree("list", "--porcelain")
        except Exception as e:
            return {"ok": False, "error": str(e)}
        trees = []
        current: dict[str, str] = {}
        for line in raw.splitlines():
            if not line.strip():
                if current:
                    trees.append(current)
                    current = {}
                continue
            if line.startswith("worktree "):
                current["path"] = line[len("worktree "):].strip()
            elif line.startswith("HEAD "):
                current["head"] = line[len("HEAD "):].strip()[:12]
            elif line.startswith("branch "):
                current["branch"] = line[len("branch "):].strip().replace("refs/heads/", "")
            elif line == "detached":
                current["detached"] = "true"
        if current:
            trees.append(current)
        return {"ok": True, "worktrees": trees, "main": str(self.root)}

    def create(self, path: str | Path, branch: str | None = None, new_branch: bool = False) -> dict[str, Any]:
        try:
            repo = self._repo_obj()
        except RuntimeError as e:
            return {"ok": False, "error": str(e)}

        target = Path(path)
        if not target.is_absolute():
            target = (self.root.parent / target).resolve()

        if self.perms:
            result = self.perms.check(
                ActionType.GIT_COMMIT,
                f"Create worktree at {target}" + (f" (branch {branch})" if branch else ""),
                detail=str(target),
            )
            if not result.allowed:
                return {"ok": False, "error": result.reason, "skipped": True}

        try:
            args = ["add"]
            if new_branch and branch:
                args += ["-b", branch]
            elif branch:
                args += [str(target), branch]
                repo.git.worktree(*args)
                return {"ok": True, "path": str(target), "branch": branch}
            args.append(str(target))
            if branch and not new_branch:
                args.append(branch)
            repo.git.worktree(*args)
            return {"ok": True, "path": str(target), "branch": branch}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def remove(self, path: str | Path, force: bool = False) -> dict[str, Any]:
        try:
            repo = self._repo_obj()
        except RuntimeError as e:
            return {"ok": False, "error": str(e)}

        target = Path(path).resolve()
        # Never remove the main worktree silently
        if target == self.root:
            return {"ok": False, "error": "Refusing to remove the main worktree"}

        if self.perms:
            result = self.perms.check(
                ActionType.GIT_COMMIT,
                f"Remove worktree {target}" + (" (force)" if force else ""),
                detail=str(target),
            )
            if not result.allowed:
                return {"ok": False, "error": result.reason, "skipped": True}

        try:
            args = ["remove"]
            if force:
                args.append("--force")
            args.append(str(target))
            repo.git.worktree(*args)
            return {"ok": True, "removed": str(target)}
        except Exception as e:
            return {"ok": False, "error": str(e)}
