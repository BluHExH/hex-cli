"""Safe Markdown helpers for streaming assistant messages."""

from __future__ import annotations

import re
from typing import Iterable


def balance_fences_for_preview(text: str) -> str:
    """Close an open fenced code block so partial streams still render.

    Does not invent content; only appends a closing fence when the number
    of fence lines is odd.
    """
    if not text:
        return text
    # Count lines that start with ```
    fence_lines = 0
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fence_lines += 1
    if fence_lines % 2 == 1:
        return text + "\n```\n"
    return text


_CODE_FENCE_RE = re.compile(
    r"```([a-zA-Z0-9_+#.-]*)[ \t]*\n(.*?)```",
    re.DOTALL,
)


def extract_code_blocks(markdown: str) -> list[tuple[str, str]]:
    """Return list of (language, code) from complete fenced blocks."""
    out: list[tuple[str, str]] = []
    for m in _CODE_FENCE_RE.finditer(markdown or ""):
        lang = (m.group(1) or "text").strip() or "text"
        code = m.group(2)
        # strip single trailing newline common in fences
        if code.endswith("\n"):
            code = code[:-1]
        out.append((lang, code))
    return out


def last_code_block(markdown: str) -> tuple[str, str] | None:
    blocks = extract_code_blocks(markdown)
    return blocks[-1] if blocks else None


def is_near_bottom(scroll_y: float, max_scroll_y: float, threshold: float = 3.0) -> bool:
    """Whether the viewport is close enough to the bottom to auto-scroll."""
    try:
        return (max_scroll_y - scroll_y) <= threshold
    except Exception:
        return True
