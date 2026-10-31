"""Git integration tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hex_cli.config import AppConfig
from hex_cli.permissions import ActionType, PermissionManager

try:
    import git
    from git import InvalidGitRepositoryError, Repo
    HAS_GITPYTHON = True
except ImportError:
    HAS_GITPYTHON = False
    Repo = None  # type: ignore


class GitTools:
    def __init__(
        self,
        project_root: Path,
        permissions: PermissionManager,
        config: AppConfig,
    ):
        self.root = project_root.resolve()
        self.perms = permissions
        self.config = config
        self._repo: Any = None

    def _get_repo(self) -> Any:
        if not HAS_GITPYTHON:
            raise RuntimeError("GitPython is not installed")
        if self._repo is None:
            try:
                self._repo = Repo(self.root, search_parent_directories=True)
            except InvalidGitRepositoryError:
                raise RuntimeError("Not a git repository")
        return self._repo

    def is_git_repo(self) -> bool:
        try:
            self._get_repo()
            return True
        except Exception:
            return False

    def git_status(self) -> dict[str, Any]:
        try:
            repo = self._get_repo()
        except RuntimeError as e:
            return {"ok": False, "error": str(e)}

        try:
            branch = repo.active_branch.name
        except TypeError:
            branch = "(detached HEAD)"

        dirty = repo.is_dirty(untracked_files=True)
        changed = [item.a_path for item in repo.index.diff(None)]
        staged = [item.a_path for item in repo.index.diff("HEAD")]
        untracked = list(repo.untracked_files)

        return {
            "ok": True,
            "branch": branch,
            "dirty": dirty,
            "changed": changed,
            "staged": staged,
            "untracked": untracked[:50],
            "untracked_count": len(untracked),
        }

    def git_diff(self, staged: bool = False) -> dict[str, Any]:
        try:
            repo = self._get_repo()
        except RuntimeError as e:
            return {"ok": False, "error": str(e)}

        try:
            if staged:
                diff_text = repo.git.diff("--cached")
            else:
                diff_text = repo.git.diff()
        except Exception as e:
            return {"ok": False, "error": str(e)}

        max_chars = self.config.max_command_output_chars
        truncated = False
        if len(diff_text) > max_chars:
            diff_text = diff_text[:max_chars] + "\n… (diff truncated)"
            truncated = True

        return {
            "ok": True,
            "staged": staged,
            "diff": diff_text or "(no changes)",
            "truncated": truncated,
        }

    def git_commit(self, message: str) -> dict[str, Any]:
        """Stage all and commit — requires approval."""
        try:
            repo = self._get_repo()
        except RuntimeError as e:
            return {"ok": False, "error": str(e)}

        if not message or not message.strip():
            return {"ok": False, "error": "Commit message is required"}

        result = self.perms.check(
            ActionType.GIT_COMMIT,
            f"Create git commit: {message[:80]}",
            detail=message,
        )
        if not result.allowed:
            return {"ok": False, "error": result.reason, "skipped": True}

        try:
            repo.git.add(A=True)
            commit = repo.index.commit(message)
            return {
                "ok": True,
                "commit": commit.hexsha[:10],
                "message": message,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def git_push(self, remote: str = "origin", branch: str | None = None) -> dict[str, Any]:
        """Push — always high-impact, requires explicit approval."""
        try:
            repo = self._get_repo()
        except RuntimeError as e:
            return {"ok": False, "error": str(e)}

        try:
            active = branch or repo.active_branch.name
        except TypeError:
            return {"ok": False, "error": "Detached HEAD — specify a branch"}

        result = self.perms.check(
            ActionType.GIT_PUSH,
            f"Push branch '{active}' to remote '{remote}'",
            detail=f"git push {remote} {active}",
        )
        if not result.allowed:
            return {"ok": False, "error": result.reason, "skipped": True}

        try:
            repo.git.push(remote, active)
            return {"ok": True, "remote": remote, "branch": active}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def git_branches(self) -> dict[str, Any]:
        """List local branches and current branch."""
        try:
            repo = self._get_repo()
        except RuntimeError as e:
            return {"ok": False, "error": str(e)}
        try:
            current = repo.active_branch.name
        except TypeError:
            current = "(detached)"
        branches = [b.name for b in repo.branches]
        return {"ok": True, "current": current, "branches": branches}

    def git_log(self, max_count: int = 15) -> dict[str, Any]:
        """Recent commit history (read-only)."""
        try:
            repo = self._get_repo()
        except RuntimeError as e:
            return {"ok": False, "error": str(e)}
        try:
            commits = []
            for c in repo.iter_commits(max_count=max_count):
                commits.append({
                    "sha": c.hexsha[:10],
                    "message": (c.message or "").strip().splitlines()[0][:120],
                    "author": str(c.author),
                    "date": c.committed_datetime.isoformat() if c.committed_datetime else "",
                })
            return {"ok": True, "commits": commits}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def git_stage(self, paths: list[str] | None = None) -> dict[str, Any]:
        """Stage selected paths (or all) — requires approval."""
        try:
            repo = self._get_repo()
        except RuntimeError as e:
            return {"ok": False, "error": str(e)}

        detail = "all changes" if not paths else ", ".join(paths[:10])
        result = self.perms.check(
            ActionType.GIT_COMMIT,
            f"Stage files: {detail}",
            detail=detail,
        )
        if not result.allowed:
            return {"ok": False, "error": result.reason, "skipped": True}

        try:
            if paths:
                for p in paths:
                    repo.git.add(p)
            else:
                repo.git.add(A=True)
            return {"ok": True, "staged": paths or ["(all)"]}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def git_checkout(self, branch: str, create: bool = False) -> dict[str, Any]:
        """Switch branch with confirmation. Never force or discard without approval."""
        try:
            repo = self._get_repo()
        except RuntimeError as e:
            return {"ok": False, "error": str(e)}

        if not branch or not branch.strip():
            return {"ok": False, "error": "Branch name required"}

        result = self.perms.check(
            ActionType.GIT_COMMIT,
            f"{'Create and switch to' if create else 'Switch to'} branch '{branch}'",
            detail=branch,
        )
        if not result.allowed:
            return {"ok": False, "error": result.reason, "skipped": True}

        try:
            if create:
                repo.git.checkout("-b", branch)
            else:
                repo.git.checkout(branch)
            return {"ok": True, "branch": branch, "created": create}
        except Exception as e:
            return {"ok": False, "error": str(e)}
