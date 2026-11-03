from __future__ import annotations

from pathlib import Path


class PathGuard:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def resolve(self, user_path: str) -> Path:
        raw = Path(user_path)
        target = (self.root / raw).resolve() if not raw.is_absolute() else raw.resolve()
        try:
            target.relative_to(self.root)
        except ValueError as exc:
            raise PermissionError(f"path escapes workspace: {user_path}") from exc
        return target
