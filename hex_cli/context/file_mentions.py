"""Parse @file mentions and inject real file contents into agent context."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

SENSITIVE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "credentials.json",
    "secrets.json",
    "id_rsa",
    "id_ed25519",
    ".npmrc",
    ".pypirc",
}

_MENTION_RE = re.compile(
    r"(?<![\w.])@([A-Za-z0-9_./\\-]+(?:\.[A-Za-z0-9]+)?)"
)

MAX_FILE_BYTES = 120_000
MAX_TOTAL_BYTES = 400_000


def extract_mentions(text: str) -> list[str]:
    seen: dict[str, None] = {}
    for m in _MENTION_RE.finditer(text or ""):
        raw = m.group(1).replace("\\", "/")
        if "@" in raw:
            continue
        if re.match(r"^[^/]+\.[a-z]{2,}$", raw) and "/" not in raw and not raw.endswith(
            (".py", ".ts", ".js", ".tsx", ".jsx", ".md", ".json", ".toml", ".yml", ".yaml", ".txt", ".rs", ".go")
        ):
            continue
        seen.setdefault(raw, None)
    return list(seen.keys())


def resolve_mention(root: Path, mention: str) -> Path | None:
    root = root.resolve()
    candidate = (root / mention).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if not candidate.is_file():
        return None
    return candidate


def _is_sensitive(path: Path) -> bool:
    name = path.name.lower()
    if name in SENSITIVE_NAMES or name.startswith(".env"):
        return True
    if name.endswith((".pem", ".key", ".p12", ".pfx")):
        return True
    return False


def read_file_safe(path: Path, max_bytes: int = MAX_FILE_BYTES) -> dict[str, Any]:
    if _is_sensitive(path):
        return {
            "ok": False,
            "path": str(path),
            "error": "sensitive file blocked from automatic context injection",
        }
    try:
        size = path.stat().st_size
    except OSError as e:
        return {"ok": False, "path": str(path), "error": str(e)}
    if size > max_bytes:
        try:
            data = path.read_bytes()[:max_bytes]
            text = data.decode("utf-8", errors="replace")
            return {
                "ok": True,
                "path": str(path),
                "content": text,
                "truncated": True,
                "size": size,
            }
        except OSError as e:
            return {"ok": False, "path": str(path), "error": str(e)}
    try:
        raw = path.read_bytes()
        if b"\x00" in raw[:4096]:
            return {"ok": False, "path": str(path), "error": "binary file skipped"}
        text = raw.decode("utf-8", errors="replace")
        return {"ok": True, "path": str(path), "content": text, "truncated": False, "size": size}
    except OSError as e:
        return {"ok": False, "path": str(path), "error": str(e)}


def inject_file_context(
    user_text: str,
    project_root: Path,
    *,
    max_total: int = MAX_TOTAL_BYTES,
) -> tuple[str, list[dict[str, Any]]]:
    mentions = extract_mentions(user_text)
    if not mentions:
        return user_text, []

    blocks: list[str] = []
    meta: list[dict[str, Any]] = []
    total = 0
    for m in mentions:
        resolved = resolve_mention(project_root, m)
        if resolved is None:
            meta.append({"path": m, "ok": False, "error": "not found or outside project"})
            blocks.append(f"[File @{m}: not found or outside project root]")
            continue
        info = read_file_safe(resolved)
        rel = str(resolved.relative_to(project_root.resolve())).replace("\\", "/")
        if not info.get("ok"):
            meta.append({"path": rel, "ok": False, "error": info.get("error")})
            blocks.append(f"[File @{rel}: {info.get('error')}]")
            continue
        content = info["content"]
        if total + len(content) > max_total:
            remain = max(0, max_total - total)
            content = content[:remain]
            info["truncated"] = True
        total += len(content)
        trunc = " (truncated)" if info.get("truncated") else ""
        blocks.append(f"File: {rel}{trunc}\n```\n{content}\n```")
        meta.append({"path": rel, "ok": True, "truncated": bool(info.get("truncated")), "size": info.get("size")})
        if total >= max_total:
            break

    if not blocks:
        return user_text, meta

    context = "\n\n".join(blocks)
    augmented = (
        f"{user_text}\n\n"
        f"--- Attached file context (injected by HEX) ---\n{context}\n"
        f"--- End attached file context ---"
    )
    return augmented, meta
