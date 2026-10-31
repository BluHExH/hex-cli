"""External editor integration for long prompt composition."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path


def resolve_editor() -> str | None:
    for key in ("HEX_EDITOR", "VISUAL", "EDITOR"):
        val = os.environ.get(key)
        if val and val.strip():
            return val.strip()
    # Windows-friendly fallbacks
    if os.name == "nt":
        for cand in ("notepad", "code --wait", "cursor --wait"):
            return cand
    return None


def compose_in_external_editor(initial: str = "", suffix: str = ".md") -> str | None:
    """Open external editor; return edited text or None on cancel/failure."""
    editor = resolve_editor()
    if not editor:
        return None
    fd, path_s = tempfile.mkstemp(prefix="hex-compose-", suffix=suffix)
    path = Path(path_s)
    try:
        os.close(fd)
        path.write_text(initial or "", encoding="utf-8")
        # Support multi-word editors like `code --wait`
        cmd = editor if os.name == "nt" and not editor.startswith("code") else editor
        # Use shell only when needed for args
        if " " in editor:
            proc = subprocess.run(editor + f' "{path}"', shell=True)
        else:
            proc = subprocess.run([editor, str(path)])
        if proc.returncode not in (0, None):
            # still try to read — user may have saved
            pass
        text = path.read_text(encoding="utf-8")
        return text
    except OSError:
        return None
    finally:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
