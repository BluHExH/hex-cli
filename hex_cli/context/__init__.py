"""HEX project context: layout summary, key snippets, and @file mentions."""

from hex_cli.context.file_mentions import (
    SENSITIVE_NAMES,
    extract_mentions,
    inject_file_context,
    resolve_mention,
)
from hex_cli.context.project import (
    discover_project_summary,
    load_key_file_snippets,
)

__all__ = [
    "SENSITIVE_NAMES",
    "discover_project_summary",
    "extract_mentions",
    "inject_file_context",
    "load_key_file_snippets",
    "resolve_mention",
]
